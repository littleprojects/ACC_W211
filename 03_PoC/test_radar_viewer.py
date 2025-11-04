"""
Prof of Concept:

Read out the radar information and display it
"""

"""
This script log the CAN data and parse it with a CAN Database (DBC) to a MDF file


"""

import can
import cantools
from lib import utils
from lib.Mdf import Mdf
from lib.Logger import Logger

import tkinter as tk
import threading

#import matplotlib.pyplot as plt
#from matplotlib.gridspec import GridSpec
#import matplotlib.animation as animation
#import numpy as np

# module name for LOGGING and CONFIG
module_name = 'RADAR_LOG'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.1'

config = {
    'bus_interface': 'VN1610',
    # 'bus_interface': 'vCAN',

    'loglevel': 'INFO',  # debug
    # 'loglevel':                 'DEBUG',             # debug
    'can_0_dbc': '../02_Sensor/CAN_ARS408_id0.dbc',
    'mdf_log_file': 'log/Radarlog_' + utils.date_time_str() + '.mf4',
}

log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(config['loglevel']))

log.info('Init ' + module_name + ' ' + module_version)

db_0 = cantools.database.load_file(config['can_0_dbc'])

# mdf = Mdf(config['mdf_log_file'], log, db_0) #, save_interval=10000)

# Erstelle eine Bus-Instanz
bus = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name=config['bus_interface'])

i = 1

log.info('Start Logging to: ' + config['mdf_log_file'])
log.info(('Load DBC: ' + config['can_0_dbc']))

obj = {'NofObjects': 0}  # object list

x = [1]
y = [1]
size = [1]
color = [1]

# Window
root = tk.Tk()
root.title("Radar View")
# Canvas erstellen
canvas = tk.Canvas(root, width=600, height=500, bg="white")
canvas.pack()

canvas.create_line(100, 450, 500, 450, fill="blue", width=1)    # horizion line
canvas.create_line(300, 450, 300, 50, fill="blue", width=1)     # center line
canvas.create_line(300, 450, 300, 50, fill="blue", width=1)     # center line

def x2px(x):
    # 300 = center of screen = 600px / 2
    px = 300 + (x * 2)
    return px

def y2px(y):
    # 450 is buttom line
    px = 450 - (y * 2)
    return px

def update_ani():
    print('update')
    canvas.delete("all")

    canvas.create_line(100, 450, 500, 450, fill="blue", width=1)
    canvas.create_line(300, 450, 300, 50, fill="blue", width=1)

    for i in range(obj['NofObjects']):
        if obj.get(i):
            data = obj[i]
            #y lat quer
            #x long abstand

            canvas.create_rectangle(x2px(data['Obj_DistLong'])-2, y2px(data['Obj_DistLat']), x2px(data['Obj_DistLong'])+2, y2px(data['Obj_DistLat'])-2, fill="red")


"""
def update_ani(frame):

    global x, y, scat
    x = []
    y = []

    for i in range(obj['NofObjects']):
        if obj.get(i):
            data = obj[i]
            x.append(data['Obj_DistLat'])
            y.append(data['Obj_DistLong'])

    #scat.set_data(x, y)
    #scat = ax.scatter(x, y)
    scat.set_offsets(np.c_[x, y])
    #print(x)
    #print(y)
    return scat
"""

def cut_obj_list(length):
    global obj
    # obj = obj[:length]
    obj['NofObjects'] = length


# 0x60a
def obj_0_status(msg):
    # cut_obj_list(msg['Obj_NofObjects'])
    obj['NofObjects'] = msg['Obj_NofObjects']


# 0x60b
def obj_1_genral(msg):
    # obj_id = msg['Obj_ID']
    obj.update({msg['Obj_ID']: msg})


# 0x60a 0 Status
# 0x60b 1 General
# 0x60c 2 Quality
# 0x60d 3 Extended
# 0x60e 4 Warning
def obj_update(msg):
    obj_id = msg['Obj_ID']

    data = {}

    # get old data
    if obj.get(obj_id):
        data = obj.get(obj_id)

    # update data with new infos
    data.update(msg)

    # update dict
    obj.update({obj_id: data})

# PLOT

#fig, ax = plt.subplots()
#scat = ax.scatter(x, y)

#plt.xlim(-10,10)
#plt.ylim(0,20)


#ani = animation.FuncAnimation(fig, update_ani, interval=10, save_count=1000)

#plt.show(block=False)

# CAN loop
def can_reader():

    i = 0

    try:
        while True:

            # wait for msgs for 1 sec - is a blocking function
            msg = bus.recv(1)

            if msg:
                msg_id = hex(msg.arbitration_id)

                # try:
                decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

                if msg_id == '0x60a':
                    obj_0_status(decode_msg)

                if msg_id == '0x60b' or msg_id == '0x60c' or msg_id == '0x60d' or msg_id == '0x60e':
                    obj_update(decode_msg)

                # print(str(hex(msg.arbitration_id)) + ' ' + str(decode_msg))

                # mdf.add_signals(decode_msg)

                i += 1
                # except:
                #    pass

                if i % 100 == 0:
                    #plt.pause(0.001)
                    update_ani()

                if i == 1:
                    log.info('Recording started')

                if i % 1000 == 0:
                    log.info('Msgs: ' + str(i))

    except KeyboardInterrupt:
        log.info('Shut down bus')
        # stop bus
        bus.shutdown()

        log.info(str(i) + ' Msgs logt ')

        # if i > 0:
        # mdf.write_mdf()

        log.info('STOPPED Logging')

        print(obj)

threading.Thread(target=can_reader).start()

root.mainloop()