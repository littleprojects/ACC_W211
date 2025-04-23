"""
This program read the CAN messages from the vehicle,
interpret the data and evaluate if everything for a ACC/CC is available.

It also sends the ACC standard messages and replay to the vehicle.

If all ACC Data are there set ART_OK or ART_EIN to ON

To test the Framework of CAN msg processing.

I try to (KISS) Keep It Simple and Stupid.

Because I want so wirte it in C later for the ECU integration.
And I need to understand it later again ;)
"""

import time
import cantools
import threading

from lib import utils
from queue import Queue
from threading import Thread
from lib.Can import Can
from lib.Mdf import Mdf
from lib.Timer import Timer
from lib.Config import Config
from lib.Logger import Logger
from lib.Can_handler import CanHandler

# module name for LOGGING and CONFIG
module_name = 'BASIC_MSG_SEND'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.1'

# default module settings - all config values needs a default value
default_config = {
    'loglevel': 'INFO',  # debug
    'stats_update_time': 10,  # [sec] log stats updates - disable with 0
    'config_file': 'config.txt',

    # CAN settings
    'can_0_interface': 'vector',
    'can_0_channel': '0',
    'can_0_bitrate': '500000',
    # 'can_0_app_name':           'vCAN',             # 'VN1610' for hardware interface
    'can_0_app_name': 'VN1610',  # Hardware interface
    'can_0_dbc': 'CAN_C.dbc',  # path to DBC
    'can_0_send': True,  # enables or disables MSG sending

    # MDF Log
    'mdf_log': False,
    'mdf_log_file': 'log/Acc_' + utils.date_time_str() + '.mf4',

    # ACC setting
    'max_msg_delay': 500,       # [ms] max delay. if CAN data older: ACC switch off
    'acc_min_speed': 30,        # [kph] minimum speed for acc activation
    'acc_max_speed': 180,       # [kph] max speed for acc activation
    'acc_off_speed': 20,        # [kph] switch off acc at this speed

    # Display
    'art_trigger_time': 8000,  # [ms] show art display after a trigger

    # ACC PID Controller parameter
    'acc_p': 0,
    'acc_i': 0,
    'acc_d': 0
}

needed_msg_id_list = [
    # mandatory msgs
    0x200,  # BS (Break System) - drive direction, ESP
    0x300,  # BS - enable ART
    0x236,  # ART_LRW - Steering
    0x238,  # ART_MRM - Buttons
    0x240,  # EZS - Buttons
    0x212,  # MS - Enable ART
    0x308,  # MS - Data
    0x312,  # MS - Moments
    0x412,  # Kombi - speed
    # other msgs
    0x408,  # Kombi
    0x328,  # BS
    0x218,  # GS - Gearbox System
    0x418,  # GS
    0x210,  # MS (Motor System) - Pedal
    0x608,  # MS
    0x328,  # BS
]

# Init Logger
log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(default_config['loglevel']))

log.info('Init')

# init config dict as global variable and load config from file
# config data will load from the config file and overwrite the default values
config = Config(module_name, default_config, log).config_obj
# update Loglevel
log.info('Change Loglevel to: ' + config.loglevel)
log.setLevel(utils.parse_log_level(config.loglevel))

# MDF
mdf = Mdf(config.mdf_log_file, log, logging=config.mdf_log)

# init CAN Queues and Flags/Events
q_can_c_in = Queue()
q_can_c_out = Queue()

# STOP thread EVENT
event_stop = threading.Event()
# NEW MSG FLAG
flag_new_msg = threading.Event()

F_10Hz = threading.Event()
F_stats = threading.Event()

# init Timer and Events
T_10Hz = Timer(0.1, F_10Hz, event_stop)
T_stats = Timer(config.stats_update_time, F_stats, event_stop)

# init CAN Communication
can_0 = Can(config.can_0_interface,
            config.can_0_channel,
            config.can_0_bitrate,
            log,
            app_name=config.can_0_app_name,
            # filter_list=
            )

can_0.connect()

# start Threads
# 10Hz
thread_timer = Thread(target=T_10Hz.run)
thread_timer.start()
# stats
thread_stats = Thread(target=T_stats.run)
thread_stats.start()

# threat so send and receive CAN msgs
thread_can_0 = Thread(target=can_0.loop, args=(q_can_c_in,
                                               q_can_c_out,
                                               flag_new_msg,
                                               event_stop))
thread_can_0.start()

# CAN HANDLER
can_handler = CanHandler(config,
                         log,
                         mdf,
                         q_can_c_in,
                         q_can_c_out,
                         needed_msg_id_list)


def main_loop():
    try:

        while True:

            # new CAN msgs?
            if flag_new_msg.is_set():
                flag_new_msg.clear()

                # process the CAN msgs
                can_handler.new_msg()

            # 10Hz Timer Flag
            if F_10Hz.is_set():
                # reset Flag
                F_10Hz.clear()

                # Todo Check msgs

                can_handler.send_art_msg()

                # break the loop if stop flag was set (Kill the main loop)
                if event_stop.is_set():
                    break

            # Status Update Timer Flag
            if F_stats.is_set():
                F_stats.clear()

                # request status update
                can_handler.status_log()

            # create some cpu idle time
            time.sleep(0.0001)

    # interrupt to stop the processes
    except KeyboardInterrupt:
        # stop Threads
        event_stop.set()


if __name__ == "__main__":
    # do the magic
    main_loop()

    # shutdown
    log.info('stop threads')

    thread_timer.join()
    thread_can_0.join()

    log.info(q_can_c_in.qsize())

    log.info('Shut down bus')
    can_0.shutdown_connection()

    # write MDF log file
    mdf.write_mdf()

    log.info('STOPPED')
