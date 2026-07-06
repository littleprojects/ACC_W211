"""
This is a Pilot or MVP (Minimum Vialble Product) of an ACC (Adaptive Cruise Control).

# Queues are used as a thread save method to share CAN data between different threads.

# CAN class
# Reads raw CAN Msgs from the bus and add it the in queue.
# Write raw CAN Msgs from out queue to the CAN bus

# CAN_handler
# Interprets the raw CAN Msgs in the in queue
# And creates raw CAN Msgs for the out queue

Todo:
- set CAN MSGs filter do reduce load on can_0 (CAN_C)

"""

import time
import threading

from lib import utils
from lib import Logger
from lib.Can import Can
from lib.Art import ART
#from lib.Mdf import Mdf
from lib.Config import Config
from lib.Art_Data import ArtData
from lib.Can_Handler import CanHandler

from lib.DataServer import DataServer

# module name for LOGGING and CONFIG
module_name = 'MVP'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.1.0'

# default module settings - all config values needs a default value
default_config = {

    'config_file': 'config.txt',
    
    'MAIN': {
        'version': '0.1.0',  # version
        'comment': 'refactoring',     # add a comment to this version, this will be added to the log file
        
        'loglevel': 'DEBUG',  # info, debug; with debug also config info will be printed out
        
        'persistent_storage_file': 'pers_store.dat',  # path and file name to persistent storage file
        'stats_update_time': 10,  # [sec] log stats updates - disable with 0
    },

    # CAN settings
    #'can_interface': 'vector',
    #'can_app_name': 'VN1610',  # Hardware interface
    #'can_app_name': 'vCAN',  # virtual CAN interface

    # Vehicle CAN
    'CAN_0': {
        #'app_name': 'VN1610',  # Hardware interface
        'app_name': 'vCAN',  # virtual CAN interface

        'interface': 'vector',
        'channel': '0',
        'bitrate': '500000',  # 5k baude
        'dbc': 'dbc/CAN_C.dbc',  # path to DBC

        'send': True,  # enables or disables MSG sending
    },

    # Radar CAN
    'CAN_1': {
        #'app_name': 'VN1610',  # Hardware interface
        'app_name': 'vCAN',  # virtual CAN interface

        'interface': 'vector',
        'channel': '1',
        'bitrate': '500000',  # 5k baude
        'dbc': 'dbc/CAN_ARS408_id0.dbc', # path to DBC

        'send': True,  # enables or disables MSG sending
    },

    # MDF Log
    'MDF': {
        'log': False,
        'log_file': 'log/ACC_' + utils.date_time_str() + '.mf4',
        'auto_save': False,     # save MDF after ACC deactivation
    },

    # Display HMI
    'HMI': {
        'art_trigger_time': 8000,  # [ms] show art display after a trigger
        'lever_hold_time': 1000,  # [ms] button holding time to re-trigger action
        'warning_time': 200,  # [ms] warning beep duration time
    },

    # ACC Settings & Limits
    'ACC': {
        'max_msg_delay': 500,       # [ms] max delay. if CAN data older: ACC switch off
        'acc_min_speed': 30,        # [kph] minimum speed for ACC activation
        'acc_max_speed': 180,       # [kph] max speed for ACC activation
        'acc_off_speed': 20,        # [kph] switch off ACC at this speed
        'acc_off_acc': 4,           # [m/s²] switch off ACC if acceleration is too high
        'acc_off_dec': 3,           # [m/s²] switch off ACC if deceleration is too high
        'acc_pause_nm_delta': 15,  # [Nm] pause if ACC_Nm - Driver_Nm > Pause_Nm_delta
        'acc_pause_lat_acc': 2,     # [m/s²] pause ACC if side (lat) acceleration in corners is high
        'acc_off_lat_acc': 3,       # [m/s²] switch ACC off if side (lat) acceleration in corners is too high

        # ACC PID Controller parameter
        'art_reg_enabled': True,  # enable/disable ART acceleration output
        'art_bre_enabled': True,  # enable/disable ART deceleration output
        #'acc_kp': 2,
        #'acc_ki': 0.03,
        #'acc_kd': 0.02,

        # Error Limitation - limit max error to smooth controller
        # Error = target_speed - current_speed
        #'pid_error_limit': True,   # enable/disable function
        #'pid_error_max': 40,        # acceleration error
        #'pid_error_min': -30,       # deceleration error

        # Rate Limit by Acc - Anti wind up function - clamp output and integral
        'acc_acceleration_limit': False,  # enable/disable acceleration limits
        'acc_max_acceleration': 2,  # [m/s²] maximal acceleration
        'acc_max_deceleration': 2,  # [m/s²] maximal deceleration

        # Rate Limit by Nm - Anti wind up function - limit output
        'acc_rate_limit': False,    # enable/disable Rate Limit
        'acc_max_acc_rate': 20,     # [Nm/s] maximal acceleration rate
        'acc_max_dec_rate': 20,     # [Nm/s] maximal deceleration rate

        # Moment Limits - Anti wind up - Limit output - CAN signal limits
        'max_acc_moment': 320,      # [Nm] maximal acceleration moment - max 800 by CAN signal (13bit * 0.1)
        'max_dec_moment': 100,      # [Nm] maximal deceleration moment - max 400 by CAN signal (12bit * 0.1)
    },

    # Limiter functions
    'LIM': {
        'lim_reg_enabled': False,    # enable/disable LIMITER controller

        # Limiter Settings
        'lim_max_speed': 250,       # [kph] max speed allowed with limiter
        'lim_min_speed': 10,        # [kph] min speed of limiter
    },

    # CAN filter list
    'filter_msg_id_can_c': [
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
    ],

    # Data Server
    # The data server is a Flask server that can be used to display the ACC data in a web browser.
    # NOTE: Use it only for testing and debugging, not in production. It is not secure and can be a security risk.
    'DATA_SERVER': {
        'enabled': True,  # enable/disable Flask server
        'host': 'localhost',  # Flask server host
        'port': 5001,  # Flask server port
    }
}

# Init Logger
log = Logger.Log(module_name).get_logger()
log.setLevel(Logger.parse_log_level(default_config['MAIN'].get('loglevel')))

log.info('Init')

# init config dict as global variable and load config from file
# config data will load from the config file and overwrite the default values
config_reader = Config(default_config, log)
config = config_reader.config_obj

# update Loglevel
log.info('Change Loglevel to: ' + config.MAIN.loglevel)
log.setLevel(Logger.parse_log_level(config.MAIN.loglevel))

log.info('Version: ' + config.MAIN.version)
if config.MAIN.comment is not None:
    log.info('Comment: ' + config.MAIN.comment)

#log.debug('New Config: ' + str(config_reader.print_config()))

# MDF
#mdf = Mdf(config.mdf_log_file, log, recording=config.mdf_log)

# Data class to handle the data exchange between the different modules
art_data = ArtData(config, log)

# ART class to handle the ART state machine and controller
#art = ART(config, log, art_data)

# Thread list to manage (start/stop) all threads
thread_list = []

# Stop thread event flag
stop_event = threading.Event()

# replaced by RepeatTimer class
# timed interval task scheduler
#def run_task(interval, func, stop_event_flag):
#    """runs func at interval [sec], until stop_event is set"""
#
#    # Todo: check if this is the best way to do this, maybe use Timer class
#    while not stop_event_flag.is_set():
#        func()
#        time.sleep(interval)

# decorator class to repeat a function at a given interval
class RepeatTimer(threading.Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)

def task_10hz():
    log.debug('10Hz Tick')

    # do the MAGIC 10 times per second
    try:
        pass
        #can_handler.send_art_msg()
        # Process the CAN msgs
        #can_c_parser.parse_msgs()

        # ART Calc
        #art.tick_10Hz()

        # send the CAN msgs
        #art_msgs = art_data.get_art_values()
        #can_c_parser.send_msg(0x250, art_msgs)
        #can_c_parser.send_msg(0x258, art_msgs)

        # log to MDF

    except Exception as e:
        log.exception(e)


def task_status_log():
    # request status update
    log.debug('Request Status log')
    log.info('CAN_C ' + can_c_parser.status())
    log.info('ART ' + art_data.status())
    log.info(art_data.get_vehicle_msgs())

# init CAN Communication
#can_0 = Can(config.can_interface, config.can_0_channel, config.can_0_bitrate, log, config.can_app_name, stop_event)
#can_1 = Can(config.can_interface, config.can_1_channel, config.can_1_bitrate, log, config.can_app_name, stop_event)
can_0 = Can(config.CAN_0, log, stop_event)
can_1 = Can(config.CAN_1, log, stop_event)


can_0.connect()
can_1.connect()

# threat so send and receive CAN msgs
thread_can_0 = threading.Thread(target=can_0.loop, args=(art_data.q_can_c_in, art_data.q_can_c_out)) # daemon=True
thread_can_0.name = 'CAN C read/write Loop'
thread_list.append(thread_can_0)

thread_can_1 = threading.Thread(target=can_1.loop, args=(art_data.q_radar_in, art_data.q_radar_out)) # daemon=True
thread_can_1.name = 'CAN R read/write Loop'
thread_list.append(thread_can_1)

# timed threads
#thread_10hz = threading.Thread(target=run_task, args=(0.1, task_10hz, stop_event))
#thread_status = threading.Thread(target=run_task, args=(config.stats_update_time, task_status_log, stop_event))

# Timer dont repeat
thread_10hz = RepeatTimer(0.1, task_10hz)
thread_10hz.name = '10Hz Tick'
thread_list.append(thread_10hz)

thread_status = RepeatTimer(float(config.MAIN.stats_update_time), task_status_log)
thread_status.name = 'Status Log'
thread_list.append(thread_status)

# CAN HANDLER - CAN parser 
can_c_parser = CanHandler(config,
                         log,
                         art_data.q_can_c_in,
                         art_data.q_can_c_out,
                         config.CAN_0.dbc,
                         art_data.set_vehicle_msgs,
                         config.filter_msg_id_can_c
                         )

# TODO can radar parser

# data server Flask
data_server = DataServer(config.DATA_SERVER, log, art_data)
thread_data_server = threading.Thread(target=data_server.run, daemon=True)
thread_data_server.name = 'Data Server'
if config.DATA_SERVER.enabled:
    thread_list.append(thread_data_server)

# start thread from list
for thread in thread_list:
    log.info('Start Thread: ' + thread.name)
    thread.start()

def main_loop():

    try:

        while not stop_event.is_set():

            # check for new messages and process them
            #can_handler.new_msg()  # process the CAN msgs

            # check CAN Queues to parse and send CAN msgs
            can_c_parser.parse_msgs()  # process the CAN msgs

            """             
            # new CAN msgs?
            if flag_new_msg.is_set():
                flag_new_msg.clear()

                # process the CAN msgs
                try:
                    can_handler.new_msg()
                except Exception as e:
                    log.exception(e)
            """

            # create some cpu idle time
            time.sleep(0.01)

    # interrupt to stop the processes
    except KeyboardInterrupt:
        # stop Threads
        stop_event.set()


# MAIN 
if __name__ == "__main__":
    # do the magic
    try:
        main_loop()
    except Exception as e:
        log.exception(e)

    # shutdown threads
    log.info('Stop Threads')
    for thread in thread_list:        
        try:
            if hasattr(thread, 'cancel'):
                log.debug('Stop Timer: ' + thread.name)
                thread.cancel()  # stop Timer

            log.debug('Stop Thread: ' + thread.name)
            thread.join(timeout=1)

            if thread.is_alive():
                log.warning('Thread did not stop: ' + thread.name)
        except Exception as e:
            log.exception(e)

    log.info('Shut down bus')
    can_0.shutdown_connection()
    can_1.shutdown_connection()

    # write MDF log file
    #mdf.write_mdf()

    log.info('STOPPED - over and out')
