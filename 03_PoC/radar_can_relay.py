
"""
PoC of a CAN Relay for the radar.

Relay Speed and Yaw from vehicle to the radar. From can0 to can1
"""

import can
import cantools

from lib import utils
from lib.Logger import Logger

# module name for LOGGING and CONFIG
module_name = 'RADAR_RELAY'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.2'

config = {
    'bus_interface': 'VN1610',
    #'bus_interface': 'vCAN',

    'loglevel': 'INFO',  # debug
    # 'loglevel':                 'DEBUG',             # debug
    'can_0_dbc': 'dbc/CAN_C.dbc',   # vehicle CAN
    'can_1_dbc': 'dbc/CAN_ARS408_id0.dbc', # radar CAN

    # filter
    'yaw_filter_size': 3    # moving average filter (min: 1)
}

# create moving average list
yaw_filter_list = [0] * config['yaw_filter_size']

log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(config['loglevel']))

log.info('Init ' + module_name + ' ' + module_version)

# load DBC
log.info('Load DBC')
db_0 = cantools.database.load_file(config['can_0_dbc'])
db_1 = cantools.database.load_file(config['can_1_dbc'])

# start CAN
log.info('init CAN bus')
bus0 = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name=config['bus_interface'])
bus1 = can.interface.Bus(channel='1', interface='vector', bitrate=500000, app_name=config['bus_interface'])

# PI config
# bus0 = can.interface.Bus(channel='can0', interface='socketcan', bitrate=500000)
# bus1 = can.interface.Bus(channel='can1', interface='socketcan', bitrate=500000)

# 0x300 speed
def relay_speed(vehicle_msg):

    speed = vehicle_msg.get('V_ANZ')

    # km/h to m/s
    speed_ms = speed / 3.6

    # speed direction
    # 0 - stand still
    # 1 - forward
    # 2 - backward

    direction = 0x0

    if speed > 0:
        direction = 0x1

    # Todo: reverse -> direction = 3

    # create message Data 2 bytes
    speed_msg_data = db_1.encode_message('SpeedInformation', {
        'RadarDevice_SpeedDirection': direction,
        'RadarDevice_Speed': speed_ms
    })

    # fill up to 8 bytes
    # speed_msg_data += b'\xFF\xFF\xFF\xFF\xFF\xFF'
    # speed_msg_data += b'\x00\x00\x00\x00\x00\x00'

    #print(speed_msg_data)

    can_msg = can.Message(arbitration_id=0x300, dlc=2, is_extended_id=False, data=speed_msg_data) #

    #print(can_msg)

    bus1.send(can_msg)

    log.debug('send ' + str(speed))


# 0x301 yaw
def relay_yaw(can_msg):

    yaw = can_msg.get('GIER_ROH')   # deg/s

    # YAW correction
    # yaw += 131

    # smooth data
    # add to list at end of list
    yaw_filter_list.append(yaw)
    # delete fist element
    yaw_filter_list.pop(0)
    # calc average
    yaw = sum(yaw_filter_list) / len(yaw_filter_list)

    yaw_msg_data = db_1.encode_message('YawRateInformation', {
        # ToDo -> offset correction first
        'RadarDevice_YawRate': yaw,
        #'RadarDevice_YawRate': 0,  # send zero
    })

    # fill up to 8 bytes
    # yaw_msg_data += b'\x00\x00\x00\x00\x00\x00'

    can_msg = can.Message(arbitration_id=0x301, is_extended_id=False, data=yaw_msg_data)

    bus1.send(can_msg)

    log.debug('send ' + str(yaw))


# msg count
i = 1

try:

    log.info('Start CAN loop')

    # CAN Loop
    while True:
        # wait for msgs for 1 sec - is a blocking function
        msg = bus0.recv(1)

        if msg:
            msg_id = hex(msg.arbitration_id)

            # speed V_ANZ on 0x412
            if msg_id == '0x412':
                decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)
                relay_speed(decode_msg)  # send 0x300 dlc=2

                i += 1

            # yaw GIER_ROH on 0x300 with DLC=8  / DLC=2 is the speed signal
            if msg_id == '0x300' and msg.dlc == 8:
                decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)
                relay_yaw(decode_msg)  # send 0x301

                i += 1

            if i % 1000 == 0:
                log.info('Msgs: ' + str(i))
                i += 1  # +1 so it will not show this multiple times


except KeyboardInterrupt:
    log.info('Shut down CAN')
    # stop bus
    bus0.shutdown()
    bus1.shutdown()

log.info('STOPPED ' + module_name)
