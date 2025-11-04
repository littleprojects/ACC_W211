"""
Prof of Concept:

Read out the radar information and display it
This script print the CAN data and parse it with a CAN Database (DBC)
"""

import can
import cantools
from lib import utils
# from lib.Mdf import Mdf
# from lib.printger import printger

import math
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import animation

# module name for printGING and CONFIG
module_name = 'RADAR_VIEW'
# just the Version of this script, to display and print; update this at major changes
module_version = '0.0.1'

config = {
    # 'bus_interface': 'VN1610',
    'bus_interface': 'vCAN',

    'printlevel': 'INFO',  # debug
    # 'printlevel':                 'DEBUG',             # debug
    'can_0_dbc': 'dbc/CAN_CAN_ARS408_id0.dbc',
    #'mdf_print_file': 'print/' + module_name + '_' + utils.date_time_str() + '.mf4',
}

# print = printger(module_name).printger
# print.setLevel(utils.parse_print_level(config['printlevel']))

# print('Init ' + module_name + ' ' + module_version)

# print(('Load DBC: ' + config['can_0_dbc']))
db_0 = cantools.database.load_file(config['can_0_dbc'])

# not used now
# mdf = Mdf(config['mdf_print_file'], print, db_0) #, save_interval=10000)

# CAN Bus-Instanz
print(('Start CAN: ' + config['bus_interface']))
bus = can.interface.Bus(channel='1', interface='vector', bitrate=500000, app_name=config['bus_interface'])

obs = {'status': {},
       'obj': {}
       }

obj_data = {
    '1': {'x': 1, 'y': 5, 'w': 2, 'angle': 0},
    '2': {'x': 10, 'y': 50, 'w': 2, 'angle': 0},
    '3': {'x': -10, 'y': 150, 'w': 2, 'angle': 10},
}

fig = plt.figure(figsize=(6, 6))
plt.axis('equal')
plt.axis([-100, 100, 0, 200])
plt.grid()

ax = plt.gca()


# ax.axis('equal')
# ax.set_aspect('equal')
# ax.set(xlim=(-100, 100), ylim=(0, 255))


# set_aspect('equal',
# ax.tick_params(axis='x', which='major', length=1)
# ax.xaxis.set_major_locator(ticker.MultipleLocator(20))


def yaw2r(yaw_ds, speed_kph):
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


def point_to_polyline_distance(P, polyline):
    """Berechnet den minimalen Abstand von Punkt P zu einem Linienzug und gibt den nächsten Punkt zurück
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
    return min_distance, closest_point
    # return dist, cp


def corner_coordinates(radius, offset=0):
    # is straight
    if radius == 0:
        return [[0 + offset, 0], [0 + offset, 260]]

    if radius > 0:
        points = []
        for i in range(0, 100):
            x = round(-radius + offset + radius * math.cos(i / 50), 2)
            y = round(radius * math.sin(i / 50), 2)

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
            x = round((-radius + offset + radius * math.cos(i / 50)), 2)
            y = round((-radius * math.sin(i / 50)), 2)

            points.append([x, y])

            # limit line when out of range
            if y > 300 or y < -300:
                break
            if x > 60 or x < -60:
                break

        return points


def target_selector(radius, object_list, dist):
    line = corner_coordinates(radius)

    new_line = []
    for i in range(len(line)):
        new_line.append((line[i][0], line[i][1]))

    dist_list = []
    cp_lines = []
    target_obj = None

    # print(object_list)

    # calc for all obj sort by distance
    for key in object_list:
        obj = object_list.get(key)

        # print('---------')
        # print(obj)

        # if target_obj == None:
        #    target_obj = obj

        # skip if coordiantes missing
        if obj.get('Obj_DistLong') is None or \
                obj.get('Obj_DistLat') is None:
            continue

        # set default if data missing
        if obj.get('Obj_Width') is None:
            obj['Obj_Width'] = 2

        if obj.get('Obj_Length') is None:
            obj['Obj_Length'] = 2

        if obj.get('Obj_OrientationAngle') is None:
            obj['Obj_OrientationAngle'] = 0

        if obj.get('Obj_Class') is None:
            obj['Obj_Class'] = '?'

        # print('---------')
        # print(obj)

        # object coordinates
        x = obj.get('Obj_DistLat') + obj.get('Obj_Width') / 2
        y = obj.get('Obj_DistLong')

        # get the shortest distance and closest point
        dist, cp = point_to_polyline_distance((x, y), new_line)

        # add to list
        dist_list.append(dist.item())
        cp_lines.append({'x1': x, 'y1': y, 'x2': cp[0].item(), 'y2': cp[1].item(), 'obj_id': key, 'obj': obj})

        # target selection
        if target_obj is None:
            if abs(dist) < 2 + obj.get('Obj_Width') / 2:
                target_obj = obj

    # print(dist_list)

    return dist_list, cp_lines, target_obj


# print(target_selector(obj_data))


def init():
    # initialize an empty list of obj
    return []


def animate(i):
    # print("animate running...")
    fig.patches = []
    # draw circles, select to color for the circles based on the input argument i.
    someColors = ['r', 'b', 'g', 'm', 'y']
    patches = []
    # for x in range(0,nx):
    # for y in range(0,ny):

    # static objects
    """
    patches.append((ax.add_patch(plt.arrow(
        x=0,
        y=0,
        dx=0,
        dy=300,
        width=1,
    ))))
    """
    # radar field
    patches.append(
        ax.add_patch(plt.Polygon(
            [[0, 0], [35, 20], [45, 55], [10, 70], [25, 150], [17, 250],
             [-17, 250], [-25, 150], [-10, 70], [-45, 55], [-35, 20]],
            closed=True,
            # facecolor='blue',
            edgecolor='red',
            alpha=0.2,
        ))
    )

    # straight lines
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(0, 1),
            closed=False,
            facecolor='blue',
            edgecolor='black'
        ))
    )
    patches.append(
        ax.add_patch(plt.Polygon(
            corner_coordinates(0, -1),
            closed=False,
            edgecolor='black'
        ))
    )

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
    """

    """
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
    """

    # circle
    # patches.append(ax.add_patch(plt.Circle((i+0.5,i+0.5),0.45,color=someColors[i % 5])))

    """
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

    # Path
    # coner simulation
    """
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

    obj_list = obs.get('obj')

    dist, obj_lines, target_obj = target_selector(0, obj_list, dist=2)

    # target_obj = None

    for i in range(len(obj_lines)):
        # print(i)

        obj = obj_lines[i]

        color = 'black'
        if abs(dist[i]) < 2:
            color = 'red'

            # if target_obj is None:
            #    target_obj = obj.get('obj')

        # line to path
        patches.append(
            ax.add_patch(plt.Polygon(
                [[obj.get('x1'), obj.get('y1')],
                 [obj.get('x2'), obj.get('y2')]],
                closed=False,
                facecolor=None,
                fill=False,
                # facecolor='blue',
                edgecolor=color
                # alpha=0.2,
            ))
        )

        obj_rct = obj.get('obj')

        color = 'blue'
        if abs(dist[i]) < 2 + obj_rct.get('Obj_Width') / 2:
            color = 'green'

            # if target_obj is None:
            #    target_obj = obj_rct

        # x = long (Distance) + 1,95m
        # y = lat (+left, -right)

        # box
        patches.append(ax.add_patch(plt.Rectangle(
            (obj_rct.get('Obj_DistLat') - obj_rct.get('Obj_Width') / 2, obj_rct.get('Obj_DistLong')),  # x, y
            obj_rct.get('Obj_Width') * 2,  # width
            obj_rct.get('Obj_Length') * 2,  # height
            angle=obj_rct.get('Obj_OrientationAngle'),
            rotation_point='center',
            color=color,
            # edgecolor='k' # k = black
            # color=someColors[i % 5]
        )))

        # """
        # text
        patches.append(ax.text(
            obj_rct.get('Obj_DistLat') + 4,  # x
            obj_rct.get('Obj_DistLong'),  # y
            str(str(obj_rct.get('Obj_ID')) + ' ' + str(obj_rct.get('Obj_Class'))),  # text
        ))
        # """

    # Target obj
    if target_obj is not None:
        patches.append(ax.add_patch(plt.Rectangle(
            (target_obj.get('Obj_DistLat') - target_obj.get('Obj_Width') / 2, target_obj.get('Obj_DistLong')),  # x, y
            target_obj.get('Obj_Width') * 2,  # width
            target_obj.get('Obj_Length') * 2,  # height
            angle=target_obj.get('Obj_OrientationAngle'),
            rotation_point='center',
            color='r',
            # edgecolor='k' # k = black
            # color=someColors[i % 5]
        )))

    """
    patches.append(ax.add_patch(plt.Rectangle(
        (i, i),     # x, y
        1,  # width
        1,  # height
        angle=i,
        color=someColors[i % 5])))
    """

    return patches


# 0x60a 0 Status
# 0x60b 1 General
# 0x60c 2 Quality
# 0x60d 3 Extended
# 0x60e 4 Warning

# 0x201 (1Hz) & 0x60a (>10Hz) status
def obj_0_status(msg):
    # cut_obj_list(msg['Obj_NofObjects'])
    obs['status'].update(msg)

    # obs['NofObjects'] = msg['Obj_NofObjects']

    # run cleanup
    obj_cleanup()


# obsolet -> integrated in obj_updater
# 0x60b general
# def obj_1_genral(msg):
#    # obj_id = msg['Obj_ID']
#    obs.update({msg['Obj_ID']: msg})

# Object List
# 0x60b-c general, quality, extended
def obj_update(msg):
    ts = utils.ts_ms()
    obj_id = msg['Obj_ID']

    data = {}

    # get old data
    if obs['obj'].get(obj_id):
        data = obs['obj'].get(obj_id)

    # add timestamp
    data['ts'] = ts

    # update data with new infos
    data.update(msg)

    # update dict
    obs['obj'].update({obj_id: data})


# delete old and incomplete objs
def obj_cleanup(delay_ms=500):
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


def can_reader():
    i = 0

    try:
        # receive loooooooping
        while True:

            # wait for msgs for 1 sec - is a blocking function
            msg = bus.recv(1)

            if msg:
                msg_id = hex(msg.arbitration_id)

                # try:
                # decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

                if msg_id == '0x201':
                    decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)
                    obj_0_status(decode_msg)

                if msg_id == '0x60a':
                    decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)
                    obj_0_status(decode_msg)

                if msg_id == '0x60b' or msg_id == '0x60c' or msg_id == '0x60d' or msg_id == '0x60e':
                    decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)
                    obj_update(decode_msg)

                # print(str(hex(msg.arbitration_id)) + ' ' + str(decode_msg))

                # mdf.add_signals(decode_msg)

                i += 1
                # except:
                #    pass

                if i % 100 == 0:
                    # plt.pause(0.001)
                    # update_ani()
                    plt.pause(0.001)
                    # print(obs)

                if i == 1:
                    print('Recording started')

                if i % 1000 == 0:
                    print('Msgs: ' + str(i))

    except KeyboardInterrupt:
        print('Shut down bus')
        # stop bus
        bus.shutdown()

        print(str(i) + ' Msgs printt ')

        # if i > 0:
        # mdf.write_mdf()

        print('STOPPED printging')

        print(obs)


'''
blit=True
Static Background: All non-changing elements of the plot (like axes, labels, or static lines) are rendered once and stored as a background image.
Dynamic Updates: For each frame, only the parts of the plot that change (like moving points or lines) are redrawn on top of the static background.
Efficiency: This reduces the computational load, making animations faster and smoother. 
'''
anim = animation.FuncAnimation(fig, animate, interval=100, save_count=2, blit=True)
plt.show(block=False)

can_reader()

print(obs)

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
