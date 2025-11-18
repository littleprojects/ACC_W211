"""
Prof of Concept:

Read out the radar information and display it
This script print the CAN data and parse it with a CAN Database (DBC)

Target selector:

Stage1:
Find the closest obj on path - instable and find and lose target quickly
Stage2:
Lock in and out of obj by time and dist
Stage3:
Obj history analyse, is it toggeling arount driving path at higher distance

"""

import can
import cantools
# from lib import utils

import math
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import animation

from lib import utils

import threading

# module name for printGING and CONFIG
module_name = 'RADAR_VIEW'
# just the Version of this script, to display and print; update this at major changes
module_version = '0.0.2'

config = {
    # 'bus_interface': 'VN1610',
    'bus_interface': 'vCAN',

    'printlevel': 'INFO',  # debug
    # 'printlevel':                 'DEBUG',             # debug

    # CAN Databases
    'can_0_dbc': 'dbc/CAN_C.dbc',
    'can_1_dbc': 'dbc/CAN_ARS408_id0.dbc',

    # Filter
    'filter_dist_2_vehicle': 100,  # objects how are far away from vehicle (Look at Lat pos)
    'filter_dist_2_path': 10,  # object how are far away from the driving path
    'filter_dyn_prop_list': [0x1, 0x3, 0x4],  # see dyn_prop list

    # display
    'skip_hidden_objs': False,

    # target lock in/out
    'dist_t_path': 1,   # [m]
    'lock_in_increase': 10,     #
    'lock_in_decrease': 4,     #
    'lock_in_active': 30,    #
}

dyn_prop = {
    0x0: 'moving',
    0x1: 'stationary',
    0x2: 'oncoming',
    0x3: 'stationary candidate',
    0x4: 'unknown',
    0x5: 'crossing stationary',
    0x6: 'crossing moving',
    0x7: 'stopped',
}

obj_class = {
    0x0: 'point',
    0x1: 'car',
    0x2: 'truck',
    0x3: 'not in use',
    0x4: 'motorcycle',
    0x5: 'bicycle',
    0x6: 'wide',
    0x7: 'reserved',
}

print('Init ' + module_name + ' ' + module_version)

print(('Load DBC: ' + config['can_0_dbc']))
db_0 = cantools.database.load_file(config['can_0_dbc'])     # vehicle CAN
db_1 = cantools.database.load_file(config['can_1_dbc'])     # radar CAN

# CAN Bus-Instanz
print(('Start CAN: ' + config['bus_interface']))
bus0 = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name=config['bus_interface'])  # vehicle CAN
bus1 = can.interface.Bus(channel='1', interface='vector', bitrate=500000, app_name=config['bus_interface'])  # radar CAN

# main obj list
obs = {'status': {},
       'obj': {},
       'radius': 0,
       'curvature': 0,
       'speed': 0,
       'art_dist': 0,
       'art_target_dist': 0,
       'rad_dist': 0,

       'lock_in_list': {},
       #'target_history': {}
    }

# temporary object list
new_obj = {}

fig = plt.figure(figsize=(7, 7))
plt.axis('equal')

# plt.axis([-100, 100, 0, 200]) # full size
plt.axis([-50, 50, 0, 100])  # half size
# plt.axis([-30, 30, 0, 60])  # small size

plt.grid()

ax = plt.gca()


def yaw2r(yaw_ds, speed_kph):
    # exit at standstill
    if yaw_ds == 0 or speed_kph == 0:
        # radius 0 = straight
        return 0

    speed_ms = speed_kph / 3.6
    yaw_rad = math.radians(yaw_ds)
    r = speed_ms / yaw_rad
    return r


def point_to_segment_distance(P, A, B):
    """Berechnet den Abstand von Punkt P zu Segment AB und gibt den nächsten Punkt zurück"""
    P, A, B = np.array(P), np.array(A), np.array(B)
    AB = B - A
    AP = P - A
    t = np.dot(AP, AB) / np.dot(AB, AB)
    t = np.clip(t, 0, 1)  # Begrenze auf Segment
    closest = A + t * AB
    distance = np.linalg.norm(P - closest)
    return distance, closest


def point_to_polyline_distance(P, polyline, obj_width=0):
    """returns minimal distance and point from point P to path
    P should be the center of the object, half obj width will be subtracted from the distance
    P = (2, 3)
    polyline = [(0, 0), (5, 0), (5, 5)]
    """
    min_distance = float('inf')
    closest_point = None

    for i in range(len(polyline) - 1):
        dist, cp = point_to_segment_distance(P, polyline[i], polyline[i + 1])
        if dist < min_distance:
            min_distance = dist
            closest_point = cp

    min_distance = min_distance - obj_width/2

    return min_distance, closest_point
    # return dist, cp


def corner_coordinates(radius, offset=0):
    # is straight
    if radius == 0:
        return [[0 + offset, -5], [0 + offset, 260]]

    if radius > 0:
        points = []
        for i in range(0, 100):
            x = round(-radius + offset + radius * math.cos(i / 50), 3)
            y = round((radius * math.sin(i / 50) - 5), 3)

            points.append([x, y])

            # limit line when out of range
            if y > 300 or y < -300:
                break
            if x > 60 or x < -60:
                break

        # print(points)
        return points

    if radius < 0:
        points = []
        for i in range(0, 100):
            x = round((-radius + offset + radius * math.cos(i / 50)), 3)
            y = round((-radius * math.sin(i / 50)) - 5, 3)

            points.append([x, y])

            # limit line when out of range
            if y > 300 or y < -300:
                break
            if x > 60 or x < -60:
                break

        return points


# filter
def obj_skip(obj):
    if obj.get('Obj_DistLong') is None or \
            obj.get('Obj_DistLat') is None:
        return True

    # dynamic
    if obj.get('Obj_DynProp') in config.get('filter_dyn_prop_list'):
        return True

    return False


def obj_hide(obj):

    # max range by speed 50m at 0 kph, 100m at 50 kph
    if obj.get('Obj_DistLong') > (50 + obs['speed']/2):
        return True

    # max distance
    if obj.get('Obj_DistLong') > config.get('filter_dist_2_vehicle'):
        return True

    # hide oncoming traffic
    if obj.get('Obj_VrelLong') * -3.6 > obs['speed']:
        return True

    # slow traffic DANGER
    if obj.get('Obj_VrelLong') * -3.6 > obs['speed'] * 0.9:
        return True

    # high lat, long speed
    # points

    return False


def update_lock_in_list(obj):
    """
    obj = {
            'obj_id': key,
            'line': {'x1': x, 'y1': y, 'x2': cp[0].item(), 'y2': cp[1].item(), },
            'dist': obj_dist,
            'obj': obj,
            'type': obj_type
        }
    """

    #now_ts = utils.ts_ms()

    obj_id = obj['obj_id']
    obj_dist = obj['dist']

    list_item = obs['lock_in_list'].get(obj_id)

    # obj is not in list
    if list_item is None:
        # create a new one
        list_item = obj
        # add score field
        list_item.update({'score': 0})

    #print('-------------')
    #print(list_item)

    score = list_item.get('score')
    type = list_item.get('type')

    # update score if obj is close to path
    if type > 0 and obj_dist < config['dist_t_path']:
        # increase score -> have to bigger the decreasing
        score += config['lock_in_increase']
        # limit max score
        if score > 100:
            score = 100

    # update list item
    list_item.update(obj)
    list_item['score'] = score

    # update lock list
    obs['lock_in_list'].update({obj_id: list_item})

def get_lock_in_target(obj_list):
    """
        list_item = {
                'obj_id': key,
                'line': {'x1': x, 'y1': y, 'x2': cp[0].item(), 'y2': cp[1].item(), },
                'dist': obj_dist,
                'obj': obj,
                'type': obj_type,
                'score': 0
            }
        """

    target_obj = None
    min_dist = 1000

    for item in obj_list:

        list_item = obs['lock_in_list'].get(item.get('obj_id'))

        # get score
        score = list_item.get('score')

        if score > config['lock_in_active']:
            # compare distance
            obj = list_item.get('obj')
            long_dist = obj.get('Obj_DistLong')

            if long_dist < min_dist:
                target_obj = list_item
                min_dist = long_dist

    # clean up list
    clean_up_id_list = []

    for key in obs['lock_in_list']:
        # decrease score
        score = obs['lock_in_list'][key]['score']
        if score > 0:
            obs['lock_in_list'][key]['score'] = score - config['lock_in_decrease']

        if score <= 0:
            clean_up_id_list.append(key)

    # clean list
    for id_item in clean_up_id_list:
        del obs['lock_in_list'][id_item]

    # Todo: delete old objects
    return target_obj


def target_selector(radius, object_list, dist):
    line = corner_coordinates(radius)

    # convert line coordinates
    drive_line = []
    for i in range(len(line)):
        drive_line.append((line[i][0], line[i][1]))

    min_dist = 500
    obj_list = []
    target = None

    # print(object_list)

    # calc for all obj sort by distance
    for key in object_list:
        obj = object_list.get(key)

        # print('---------')
        # print(obj)

        # if target_obj == None:
        #    target_obj = obj

        # skip incomplete objs
        if obj_skip(obj):
            continue

        # filter function
        hide_obj = False

        if obj_hide(obj):
            hide_obj = True

            # skip
            if config.get('skip_hidden_objs'):
                continue

        # set defaults if data missing
        # todo: do in function
        if obj.get('Obj_Width') is None:
            obj['Obj_Width'] = 2

        if obj.get('Obj_Length') is None:
            obj['Obj_Length'] = 2

        if obj.get('Obj_OrientationAngle') is None:
            obj['Obj_OrientationAngle'] = 0

        if obj.get('Obj_Class') is None:
            obj['Obj_Class'] = 0

        # print('---------')
        # print(obj)

        # object coordinates
        x = -obj.get('Obj_DistLat')  # + obj.get('Obj_Width') / 2  # obj center
        y = obj.get('Obj_DistLong')
        w = obj.get('Obj_Width')

        # get the shortest distance and closest point from vehicle CENTER to drive path
        obj_dist, cp = point_to_polyline_distance((x+w/2, y), drive_line, w)

        # filter obj with too much distance to path
        if obj_dist > config.get('filter_dist_2_path'):
            hide_obj = True
            # skip this obj
            continue

        # obj type 0 = hide, 1 = normal, 2 = in lane, 3 target
        obj_type = 1

        # is obj edge close to path
        # Todo: dist_to_path can variate over dist_to_ego
        if abs(obj_dist) < dist:  # obj.get('Obj_Width') / 2):
        #if (abs(obj_dist)-(obj.get('Obj_Width') / 2)) < dist:  # obj.get('Obj_Width') / 2):
            obj_type = 2

        if hide_obj:
            obj_type = 0

        # create item
        list_item = {
            'obj_id': key,
            'line': {'x1': x, 'y1': y, 'x2': cp[0].item(), 'y2': cp[1].item(), },
            'dist': obj_dist,
            'obj': obj,
            'type': obj_type
        }

        # add to list
        obj_list.append(list_item)

        # stage1 ------------------------------------------------------------------
        # target selection with the smallest distance on driving path (type 1)
        if obj_type == 2 and y < min_dist:
            target = list_item
            # set new min dist
            min_dist = y

        # stage2 ------------------------------------------------------------------
        # lock in by time and dist
        update_lock_in_list(list_item)

        # Todo login obj in after time as target
        # Todo logout after time or dist

        # print(y)

    # print(dist_list)
    # print('---')

    # Todo: floor target dist
    target = get_lock_in_target(obj_list)

    return obj_list, target


# 0x60a 0 Status
# 0x60b 1 General
# 0x60c 2 Quality -> not needed now
# 0x60d 3 Extended
# 0x60e 4 Warning -> not needed now

# 0x201 (1Hz) & 0x60a (>10Hz) status
def obj_0_status(msg):
    # cut_obj_list(msg['Obj_NofObjects'])
    obs['status'].update(msg)

    # obs['NofObjects'] = msg['Obj_NofObjects']

    # run cleanup -> do in animation when it is needed
    # obj_cleanup()

    # print(msg)

    # errors to check
    error_list = [
        'RadarState_Persistent_Error',
        'RadarState_Interference',
        'RadarState_Temperature_Error',
        'RadarState_Temporary_Error',
        'RadarState_Voltage_Error',
        'RadarState_RadarPowerCfg',
        'RadarState_MotionRxState',
    ]

    # check for errors
    for item in error_list:
        if msg.get(item) != 0:
            print(item)

    """
    'RadarState_Persistent_Error':  0 'No error', 
    'RadarState_Interference':      0 'No interference', 
    'RadarState_Temperature_Error': 0 'No error', 
    'RadarState_Temporary_Error':   0 'No error', 
    'RadarState_Voltage_Error':     0 'No error', 
    'RadarState_RadarPowerCfg':     0 'Standard',  
    'RadarState_MotionRxState': 3 'Speed and yaw rate missing', 
    """


def obj_0_status_2(msg):
    # cut_obj_list(msg['Obj_NofObjects'])
    obs['status'].update(msg)


# Object List
# 0x60b-c general, quality, extended
def obj_update(msg):
    # ts = utils.ts_ms()
    obj_id = msg['Obj_ID']

    data = {}

    # get old data
    if obs['obj'].get(obj_id):
        data = obs['obj'].get(obj_id)

    # add timestamp
    # data['ts'] = ts

    # update data with new infos
    data.update(msg)

    # update temporary obj list
    new_obj.update({obj_id: data})
    # update permanent obj list
    obs['obj'].update({obj_id: data})


def yaw_update(msg):
    # read yaw from can msg
    yaw = msg.get('GIER_ROH')
    # error handling
    if yaw is None:
        return

    # rad/sec to deg/s (1rad = 180/PI) # 180/PI = 57.2958
    yaw = yaw * 57.2958

    # offset correction
    # yaw += 131.234 # obsolete since dbc update
    # print(round(yaw, 3))

    # calibration factor
    #yaw = yaw * 1.01

    # Todo: update only on moving -> test
    # if yaw == 0 or obs['speed'] == 0:
    #    return

    # yaw to radius
    radius = yaw2r(yaw, obs['speed'])

    # print(radius)
    # curvature
    if radius == 0:
        obs['curvature'] = 0
    else:
        obs['curvature'] = 1/radius

    # update radius
    obs['radius'] = radius


def speed_update(msg):
    obs['speed'] = round(msg.get('V_ANZ'), 1)


def art_update(msg):
    obs['art_dist'] = msg.get('ABST_R_OBJ')
    obs['art_target_dist'] = msg.get('SOLL_ABST')


# delete old and incomplete objs
def obj_cleanup(delay_ms=500):
    global obs, new_obj

    # 60A start of new obj list
    # -> replace obj_list with new list to clean older obj
    obs['obj'] = new_obj
    # -> create new empty list and fill with obj
    new_obj = {}

    """
    ts = utils.ts_ms()

    obj_list = obs.get('obj')

    del_list = []

    # go through list
    for key in obj_list:
        # load single obj form list
        obj = obj_list.get(key)

        # is obj too old
        if ts - delay_ms > obj.get('ts'):
            # delete entry
            # del obs['obj'][key]
            del_list.append(key)

            # print('Obj: ' + str(key) + ' too old - del')

            # skip - next obj
            continue

        # obj is incomplete
        if obj.get('Obj_DistLong') is None or obj.get('Obj_DistLat') is None:
            # del obs['obj'][key]
            del_list.append(key)
            # print('Obj: ' + str(key) + ' incomplete - del')

    # delete elements
    for x in del_list:
        del obs['obj'][x]
    """


def radar_can_reader():
    i = 0

    print('Wait for CAN messages')

    try:
        # receive loooooooping
        while True:

            # wait for msgs for 1 sec - is a blocking function
            msg = bus1.recv(1)

            if msg:
                msg_id = hex(msg.arbitration_id)

                # try:
                # decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

                # radar status msg
                if msg_id == '0x201':
                    decode_msg = db_1.decode_message(msg.arbitration_id, msg.data,
                                                     decode_choices=False)  # dont interpret signals to string
                    obj_0_status(decode_msg, )

                # start of obj list
                if msg_id == '0x60a':
                    decode_msg = db_1.decode_message(msg.arbitration_id, msg.data, decode_choices=False)
                    obj_0_status_2(decode_msg)
                    # will overwrite obj list with a fresh one to remove old obj
                    obj_cleanup()
                    # plt.pause(0.001)

                # obj info
                if msg_id == '0x60b' or msg_id == '0x60c' or msg_id == '0x60d':  #  or msg_id == '0x60e'
                    decode_msg = db_1.decode_message(msg.arbitration_id, msg.data, decode_choices=False)
                    obj_update(decode_msg)
                    # plt.pause(0.01)

                # print(str(hex(msg.arbitration_id)) + ' ' + str(decode_msg))

                # mdf.add_signals(decode_msg)

                i += 1
                # except:
                #    pass

                if i % 100 == 0:
                    # plt.pause(0.001)
                    # update_ani()
                    # plt.pause(0.001)
                    # print(obs)
                    pass

                if i == 1:
                    print('Started')

                if i % 1000 == 0:
                    print('Msgs: ' + str(i))

            # bus idle
            # else:
            # plt.pause(0.001)


    except KeyboardInterrupt:
        print('Shut down bus')
        # stop bus
        bus1.shutdown()

        # print(str(i) + ' Msgs')

        # if i > 0:
        # mdf.write_mdf()

        print('STOPPED')

        print(obs)


def vehicle_can_reader():
    try:
        # receive loooooooping
        while True:

            # wait for msgs for 1 sec - is a blocking function
            msg = bus0.recv(1)

            if msg:
                msg_id = hex(msg.arbitration_id)

                # try:
                # decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

                # yaw rate msg
                if msg_id == '0x300' and msg.dlc == 8:
                    decode_msg = db_0.decode_message(msg.arbitration_id, msg.data,
                                                     decode_choices=False)  # dont interprese signals to string
                    yaw_update(decode_msg)

                # speed msg
                if msg_id == '0x412':
                    decode_msg = db_0.decode_message(msg.arbitration_id, msg.data,
                                                     decode_choices=False)  # dont interprese signals to string
                    speed_update(decode_msg)

                # ART msg
                if msg_id == '0x258':
                    decode_msg = db_0.decode_message(msg.arbitration_id, msg.data,
                                                     decode_choices=False)  # dont interprese signals to string
                    art_update(decode_msg)

    except KeyboardInterrupt:
        print('Shut down bus')
        # stop bus
        bus0.shutdown()


# start CAN Reader as thread
thread_r_can = threading.Thread(target=radar_can_reader)
thread_r_can.start()

thread_v_can = threading.Thread(target=vehicle_can_reader)
thread_v_can.start()


def init():
    # initialize an empty list of obj
    return []


def get_score(id):

    if obs['lock_in_list'].get(id) is None:
        return 0

    if obs['lock_in_list'][id].get('score') is None:
        return 0

    return obs['lock_in_list'][id].get('score')


# Todo: exit handler

def animate(i):
    # print("animate running...")
    # fig.patches = []
    # draw circles, select to color for the circles based on the input argument i.
    # someColors = ['r', 'b', 'g', 'm', 'y']

    # create patch list with static elements, radar objects will append later to the list
    patches = [
        # radar field filed of view
        ax.add_patch(plt.Polygon(
            [[0, 0], [35, 20], [45, 55], [10, 70], [25, 150], [17, 250],
             [-17, 250], [-25, 150], [-10, 70], [-45, 55], [-35, 20]],
            closed=True,
            # facecolor='blue',
            edgecolor='red',
            alpha=0.2,
        )),
        # straight lines right
        ax.add_patch(plt.Polygon(
            corner_coordinates(obs.get('radius'), 1),
            closed=False,
            facecolor='None',
            edgecolor='black',
            fill=False,
            linewidth=2
        )),
        # straight lines left
        ax.add_patch(plt.Polygon(
            corner_coordinates(obs.get('radius'), -1),
            closed=False,
            facecolor='None',
            edgecolor='black',
            fill=False,
            linewidth=2
        ))
    ]

    # Curved line
    """
    # corner left RED
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(2000-i),
            closed=False,
            edgecolor='red',
            facecolor=None,
            fill=False,
            linewidth=2
        ))
    )
    # corner right
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(2000-i, 1),
            closed=False,
            edgecolor='black',
            facecolor=None,
            fill=False
        ))
    )
    # corner left
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(-500-i, -1),
            closed=False,
            edgecolor='black',
            facecolor=None,
            fill=False
        ))
    )
    # corner right
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(-500-i, 1), closed=False, edgecolor='black', facecolor=None, fill=False
    )))

    # Path
    # coner simulation
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(2000 - i),
            closed=False,
            edgecolor='red',
            facecolor=None,
            fill=False,
            linewidth=2
        ))
    )
    """

    # example patch obj
    """
    # circle
    # patches.append(ax.add_patch(plt.Circle((i+0.5,i+0.5),0.45,color=someColors[i % 5])))

    # arrow example
    patches.append((ax.add_patch(plt.arrow(
        x=0,
        y=0,
        dx=0,
        dy=300,
        width=1,
    ))))

    # rectangle
    for key in obj_data:
        id = key

        obj = obj_data[id]

        # x = long (Distance) + 1,95m
        # y = lat (+left, -right)

        # box
        patches.append(ax.add_patch(plt.Rectangle(
            (obj.get('x') - obj.get('w')/2, obj.get('y')),  # x, y
            obj.get('w')*2,  # width
            obj.get('w')*2,  # height
            angle=obj.get('angle'),
            rotation_point='center',
            color='b',
            #edgecolor='k' # k = black
            #color=someColors[i % 5]
            )))

        # text
        patches.append(ax.text(
            obj.get('x') + 4,   # x
            obj.get('y'),  # y
            str(id),  # text
        ))
    """

    # copy obj dict to work with - changes can not effect the calc and display
    obj_list = obs.get('obj').copy()

    # run target_selector MAGIC create the target selector list
    ts_list, target_obj = target_selector(obs.get('radius'), obj_list, dist=config['dist_t_path'])

    # target_obj = None

    # go to obj list
    for i in range(len(ts_list)):
        # print(i)

        # load single item form list
        obj = ts_list[i]

        # normal line color
        line_color = 'black'
        obj_color = 'blue'
        fill = True

        # is obj hidden
        if obj.get('type') == 0:
            fill = False

        # is obj in path
        if obj.get('type') == 2:
            # line_color = 'red'
            obj_color = 'green'

            # if target_obj is None:
            #    target_obj = obj.get('obj')

        # load obj data
        obj_rct = obj.get('obj')

        # box
        patches.append(ax.add_patch(plt.Rectangle(
            (-obj_rct.get('Obj_DistLat') - obj_rct.get('Obj_Width') / 2, obj_rct.get('Obj_DistLong')),  # x, y
            obj_rct.get('Obj_Width'),  # width
            obj_rct.get('Obj_Length'),  # height
            angle=obj_rct.get('Obj_OrientationAngle'),
            rotation_point='center',
            color=obj_color,
            fill=fill,
            # edgecolor='k' # k = black
            # color=someColors[i % 5]
        )))

        # if hidden - no text, no line
        if fill:
            # """
            # text
            x_coor = -obj_rct.get('Obj_DistLat')
            text_align = 'left'
            if x_coor > 0:
                x_coor += obj_rct.get('Obj_Width') + 1
            else:
                x_coor += - obj_rct.get('Obj_Width') - 1
                text_align = 'right'

            patches.append(ax.text(
                x_coor,  # x
                obj_rct.get('Obj_DistLong'),  # + obj_rct.get('Obj_Length') / 2,  # y
                # str(str(obj_rct.get('Obj_ID')) + ' ' + str(obj_class.get(obj_rct.get('Obj_Class')))),  # text
                # str(dyn_prop.get(obj_rct.get('Obj_DynProp'))),  # text Dyn prop calls
                #str(obj_rct.get('Obj_VrelLong') * 3.6),  # V rel lon  ms 2 kph
                str(get_score(obj_rct.get('Obj_ID'))),
                ha=text_align,
            ))
            # """

            # get line details
            line = obj.get('line')

            # line to path
            patches.append(
                ax.add_patch(plt.Polygon(
                    [[line.get('x1'), line.get('y1')],
                     [line.get('x2'), line.get('y2')]],
                    closed=False,
                    facecolor=None,
                    fill=False,
                    # facecolor='blue',
                    edgecolor=line_color
                    # alpha=0.2,
                ))
            )

    # Target obj
    if target_obj is not None:
        # load obj data
        obj_rct = target_obj.get('obj')
        # draw box
        patches.append(ax.add_patch(plt.Rectangle(
            (-obj_rct.get('Obj_DistLat') - obj_rct.get('Obj_Width') / 2, obj_rct.get('Obj_DistLong')),  # x, y
            obj_rct.get('Obj_Width'),  # width
            obj_rct.get('Obj_Length'),  # height
            angle=obj_rct.get('Obj_OrientationAngle'),
            rotation_point='center',
            color='red',
            # edgecolor='k' # k = black
            # color=someColors[i % 5]
        )))
        # store distance
        obs['rad_dist'] = obj_rct.get('Obj_DistLong')
    else:
        # no target - reset distance
        obs['rad_dist'] = 0

    # add text details
    patches.append(
        # speed text
        ax.text(
            21,  # x
            2,  # y
            # text
            'kph ' + str(obs.get('speed')) + '\n' \
            'r  ' + str(round(obs.get('radius')))
            ,
        )
    )
    patches.append(
        ax.text(
            -39,  # x
            2,  # y
            # text
            'art  ' + str(round(obs.get('art_dist'), 1)) + '\n' \
            'rad ' + str(round(obs.get('rad_dist'), 1))
            ,
        )
    )

    # ART Target object distance
    art_dist = obs.get('art_dist')
    if art_dist > 0:
        patches.append(
            ax.add_patch(plt.Polygon(
                [[-10, art_dist], [10, art_dist]],
                closed=False,
                facecolor='None',
                edgecolor='red',
                fill=False,
                linewidth=2
            ))
        )

    # ART target distance
    art_tar_dist = obs.get('art_target_dist')
    if art_tar_dist > 0:
        patches.append(
            ax.add_patch(plt.Polygon(
                [[-10, art_tar_dist], [10, art_tar_dist]],
                closed=False,
                facecolor='None',
                edgecolor='green',
                fill=False,
                linewidth=2
            ))
        )

    """
    patches.append(ax.add_patch(plt.Rectangle(
        (i, i),     # x, y
        1,  # width
        1,  # height
        angle=i,
        color=someColors[i % 5])))
    """

    return patches


anim = animation.FuncAnimation(fig, animate, init_func=init, interval=100, save_count=2, blit=True)

plt.show()

# plt.pause(0.001)

# main loop
# can_reader()

# print(obs)

"""
{'status': {
    'Obj_NofObjects': 24, 
    'Obj_MeasCounter': 3429, 
    'Obj_InterfaceVersion': 1, 
    'RadarState_NVMwriteStatus': 'failed', 
    'RadarState_NVMReadStatus': 'successful', 
    'RadarState_MaxDistanceCfg': 250, 
    'RadarState_Persistent_Error': 'No error', 
    'RadarState_Interference': 'No interference', 
    'RadarState_Temperature_Error': 'No error', 
    'RadarState_Temporary_Error': 'No error', 
    'RadarState_Voltage_Error': 'No error', 
    'RadarState_RadarPowerCfg': 'Standard', 
    'RadarState_SortIndex': 1, 
    'RadarState_SensorID': 0, 
    'RadarState_MotionRxState': 'Speed and yaw rate missing', 
    'RadarState_SendExtInfoCfg': 'Active', 
    'RadarState_SendQualityCfg': 'Active', 
    'RadarState_OutputTypeCfg': 'SendObjects', 
    'RadarState_CtrlRelayCfg': 'Active', 
    'RadarState_RCS_Threshold': 'Standard'
    }, 
'obj': {
    35: {
        'Obj_ID': 35, 
        'Obj_CollDetRegionBitfield': 0, 

        'Obj_DistLong': 74.60000000000002, -> x
        'Obj_DistLat': 3.4000000000000057, -> y
        'Obj_Class': 'Car', 
        'Obj_OrientationAngle': -3.1999999999999886, 
        'Obj_Length': 4.4, 
        'Obj_Width': 1.8, -> w

        'Obj_VrelLong': -8.5, 
        'Obj_VrelLat': -0.5,


        'Obj_DynProp': 'Oncoming', 
        'Obj_RCS': 5.5, 
        'Obj_DistLong_rms': '<0.288 m', 
        'Obj_DistLat_rms': '<0.478 m', 
        'Obj_VrelLong_rms': '<0.371 m/s', 
        'Obj_VrelLat_rms': '<0.616 m/s', 
        'Obj_ArelLong_rms': '<1.023 m/s²', 
        'Obj_ArelLat_rms': '<0.005 m/s²', 
        'Obj_Orientation_rms': '<0.234 deg',
        'Obj_ProbOfExist': '<=100%', 
        'Obj_MeasState': 'Measured', 
        'Obj_ArelLong': 0.45000000000000107, 
        'Obj_ArelLat': 0.0,        
    }, 
    52: {'Obj_ID': 52, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 84.80000000000007, 'Obj_DistLat': 3.0000000000000284, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -0.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 13.5, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.23000000000000043, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    10: {'Obj_ID': 10, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 95.80000000000007, 'Obj_DistLat': 1.200000000000017, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.0, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 15.5, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.2699999999999996, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    32: {'Obj_ID': 32, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 120.0, 'Obj_DistLat': -1.1999999999999886, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -0.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 24.0, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.13000000000000078, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    45: {'Obj_ID': 45, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 140.80000000000007, 'Obj_DistLat': -2.9999999999999716, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.0, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 17.0, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.794 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.794 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.332 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.0600000000000005, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    17: {'Obj_ID': 17, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 152.4000000000001, 'Obj_DistLat': -6.399999999999977, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.0, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 21.5, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.616 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.02999999999999936, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    3: {'Obj_ID': 3, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 183.80000000000007, 'Obj_DistLat': -8.599999999999994, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -1.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 22.5, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.616 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.794 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.05000000000000071, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -2.799999999999983, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    8: {'Obj_ID': 8, 'Obj_CollDetRegionBitfield': 0}, 
    0: {'Obj_ID': 0, 'Obj_CollDetRegionBitfield': 0, 'Obj_DistLong': 215.60000000000002, 'Obj_DistLat': -10.799999999999983, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -1.75, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 22.5, 'Obj_DistLong_rms': '<0.478 m', 'Obj_DistLat_rms': '<0.616 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.794 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.332 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.13000000000000078, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -2.799999999999983, 'Obj_Length': 4.4, 'Obj_Width': 1.8}, 
    1: {'Obj_ID': 1, 'Obj_DistLong': 14.200000000000045, 'Obj_DistLat': -3.799999999999983, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.75, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 6.0, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.794 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.4800000000000004, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 4.4, 'Obj_Width': 1.8, 'Obj_CollDetRegionBitfield': 0}, 
    24: {'Obj_ID': 24, 'Obj_DistLong': 24.800000000000068, 'Obj_DistLat': -3.3999999999999773, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -0.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 21.5, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.371 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<0.794 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.13000000000000078, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Truck', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 12.0, 'Obj_Width': 2.2, 'Obj_CollDetRegionBitfield': 0}, 
    23: {'Obj_ID': 23, 'Obj_DistLong': 37.80000000000007, 'Obj_DistLat': -2.9999999999999716, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -0.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 20.0, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.371 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.2400000000000002, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 4.4, 'Obj_Width': 1.8, 'Obj_CollDetRegionBitfield': 0}, 
    36: {'Obj_ID': 36, 'Obj_DistLong': 42.39999999999998, 'Obj_DistLat': 11.200000000000017, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -0.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 7.0, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.620000000000001, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 4.4, 'Obj_Width': 1.8, 'Obj_CollDetRegionBitfield': 0}, 
    22: {'Obj_ID': 22, 'Obj_DistLong': 62.80000000000007, 'Obj_DistLat': -4.599999999999994, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.5, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 4.5, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.616 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.02999999999999936, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Point', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 0.2, 'Obj_Width': 0.4, 'Obj_CollDetRegionBitfield': 0}, 
    37: {'Obj_ID': 37, 'Obj_DistLong': 60.39999999999998, 'Obj_DistLat': 7.400000000000006, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.5, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 16.5, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.17999999999999972, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 4.4, 'Obj_Width': 1.8, 'Obj_CollDetRegionBitfield': 0}, 
    27: {'Obj_ID': 27, 'Obj_DistLong': 69.80000000000007, 'Obj_DistLat': 4.800000000000011, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -1.5, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 10.5, 'Obj_DistLong_rms': '<0.616 m', 'Obj_DistLat_rms': '<0.616 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<1.697 m/s', 'Obj_ArelLong_rms': '<1.317 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.669 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.0, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -2.799999999999983, 'Obj_Length': 4.4, 'Obj_Width': 1.8, 'Obj_CollDetRegionBitfield': 0}, 
    42: {'Obj_ID': 42, 'Obj_DistLong': 68.20000000000005, 'Obj_DistLat': 7.800000000000011, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': -0.25, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 2.0, 'Obj_DistLong_rms': '<0.288 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<0.794 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.1899999999999995, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Car', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 4.4, 'Obj_Width': 1.8, 'Obj_CollDetRegionBitfield': 0}, 
    14: {'Obj_ID': 14, 'Obj_DistLong': 148.0, 'Obj_DistLat': -1.3999999999999773, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.0, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 22.0, 'Obj_DistLong_rms': '<0.478 m', 'Obj_DistLat_rms': '<0.616 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.616 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.234 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.0600000000000005, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Truck', 'Obj_OrientationAngle': 3.200000000000017, 'Obj_Length': 12.0, 'Obj_Width': 2.2, 'Obj_CollDetRegionBitfield': 0}, 
    18: {'Obj_ID': 18, 'Obj_DistLong': 10.200000000000045, 'Obj_DistLat': -4.199999999999989, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.0, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 4.5, 'Obj_DistLong_rms': '<0.371 m', 'Obj_DistLat_rms': '<0.478 m', 'Obj_VrelLong_rms': '<0.371 m/s', 'Obj_VrelLat_rms': '<1.023 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.332 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.34999999999999964, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Motorcycle', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 1.6, 'Obj_Width': 1.6, 'Obj_CollDetRegionBitfield': 0}, 
    26: {'Obj_ID': 26, 'Obj_DistLong': 4.600000000000023, 'Obj_DistLat': -3.9999999999999716, 'Obj_VrelLong': -8.5, 'Obj_VrelLat': 0.0, 'Obj_DynProp': 'Oncoming', 'Obj_RCS': 5.0, 'Obj_DistLong_rms': '<0.794 m', 'Obj_DistLat_rms': '<0.371 m', 'Obj_VrelLong_rms': '<0.478 m/s', 'Obj_VrelLat_rms': '<0.478 m/s', 'Obj_ArelLong_rms': '<1.023 m/s²', 'Obj_ArelLat_rms': '<0.005 m/s²', 'Obj_Orientation_rms': '<0.165 deg', 'Obj_ProbOfExist': '<=100%', 'Obj_MeasState': 'Measured', 'Obj_ArelLong': 0.0, 'Obj_ArelLat': 0.0, 'Obj_Class': 'Truck', 'Obj_OrientationAngle': -3.1999999999999886, 'Obj_Length': 12.0, 'Obj_Width': 2.2, 'Obj_CollDetRegionBitfield': 0}}
, 'NofObjects': 14}
"""
