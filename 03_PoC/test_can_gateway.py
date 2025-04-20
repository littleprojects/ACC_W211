"""
CAN TEST

This is a testtool.
It will be installed in the CANline from vehicle to ACC Control unit.

To see that messages will be send from what side.

pip install python-can
pip install cantools
"""

import os
import can
import time
import cantools
import logging

from logging.handlers import RotatingFileHandler


config = {
    'name':             'TEST_Gateway',
    'path':             'C:/Users/u12x66/Dropbox/Projects/ACC_W211/03_PoC',
    'loglevel':         'info',
    'log_file':         True,
    'log_file_path':    'log',
    'dbc':              'CAN_C.dbc'
}

logFile = config['path'] + '/' + config['log_file_path'] + '/' + 'Log_'+config['name']+'.txt'
dbcFile = config['path'] + '/' + config['dbc']

# create log dir if not exist
if not os.path.exists(config['log_file_path']):
    os.mkdir(config['log_file_path'])

# --------- LOGGER SETUP ---------
logging.basicConfig(level=logging.INFO, # console loglevel
                    format='%(asctime)s %(name)-12s: %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    )

# log format
formatter = logging.Formatter('%(asctime)s %(name)-12s: %(levelname)-8s %(message)s', datefmt='%m-%d %H:%M:%S')

log_file_handler = RotatingFileHandler(logFile, mode='a+', maxBytes=1 * 1024 * 1024, backupCount=1, encoding=None, delay=0)
log_file_handler.setLevel(logging.INFO)  # logfile loglevel
log_file_handler.setFormatter(formatter)
logging.getLogger().addHandler(log_file_handler)


log = logging.getLogger(config['name'])

# ----------------------------------------------------

log.info('Start CAN RELAY')

log.info('config: \t' + str(config))

# load DBC
log.info('load DBC: \t' + dbcFile)

if not os.path.exists(dbcFile):
    log.critical('DBC NOT FOUND: \t' + dbcFile)
    exit()
db = cantools.database.load_file(dbcFile)

#filters = [
#    {"can_id": 0x200, "can_mask": 0x7FF, "extended": False},
#    {"can_id": 0x210, "can_mask": 0x7FF, "extended": False}
#]

# init CAN Lines
try:
    #can_0 = can.interface.Bus(interface='vector', channel=0, bitrate=500000) #, can_filters=filters)
    #can_1 = can.interface.Bus(interface='vector', channel=1, bitrate=500000) #, can_filters=filters)

    can_0 = can.interface.Bus(interface='vector', channel=0, bitrate=500000, app_name='NewApp') #, can_filters=filters)
    can_1 = can.interface.Bus(interface='vector', channel=1, bitrate=500000, app_name='NewApp') #, can_filters=filters)

except Exception as e:
    log.critical('CANT START CAN')
    log.error(e)
    log.info('EXIT Program')
    exit()

# MSG ID Lists
can_0_list = []
can_1_list = []

# Ids NOT to send to CAN1
can_0_filter_list = ['0x236', '0x250']
# Ids NOT to send to CAN0
can_1_filter_list = []


def can_relay():
    i0 = 0
    i1 = 0

    try:
        while True:
            msg_0 = can_0.recv()
            msg_1 = can_1.recv()

            if msg_0:
                msg_0_id = hex(msg_0.arbitration_id)
                
                if msg_0_id not in can_0_list:
                    # update list
                    can_0_list.append(msg_0_id)
                    log.info('CAN_0 new Id: ' + str(msg_0_id) + ' - ' + str(can_0_list))

                if not (msg_0_id in can_0_filter_list):
                    # print(f"ID: {msg_0.arbitration_id}, Daten: {msg_0.data}")
                    #can_1.send(msg_0)
                    pass

                i0 += 1
                if i0 % 1000 == 0:
                    log.info('CAN_0 ' + str(i0) + ' Mgs transmitt')

            if msg_1:
                #can_0.send(msg_1)

                msg_1_id = hex(msg_1.arbitration_id)
                
                if msg_1_id not in can_1_list:
                    # update list
                    can_1_list.append(msg_1_id)
                    log.info('CAN_1 new Id: ' + str(msg_1_id) + ' - ' + str(can_1_list))

                i1 += 1
                if i1 % 1000 == 0:
                    log.info('CAN_1 ' + str(i1) + ' Mgs transmitt')

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Programm beendet")
    finally:
        log.info('STOP')
        can_0.shutdown()

can_relay()