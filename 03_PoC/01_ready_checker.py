
"""
This programm read the CAN messages from the vehicle, 
interprete the data and evaluate if everything for a ACC is available

"""

import can
import time
import traceback
import cantools

from lib import utils
from lib import check
from lib.Logger import Logger
from lib.Config import Config
from lib.Can import Can
from lib.Mdf import Mdf


# module name for LOGGING and CONFIG
module_name = 'READY_CHECK' 
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.1'        

# default module settings
default_config = {
    'loglevel':                 'INFO',             # debug
    'stats_update_time':        10,                 # [sec] log stats updates
    'config_file':              'config.txt',
    'can_0_interface':          'vector',
    'can_0_channel':            '0',
    'can_1_channel':            '1',
    'can_0_speed':              500000,
    'can_0_dbc':                'CAN_C.dbc',
    'mdf_log':                  0,
    'mdf_log_file':             'log/ANlog_' + utils.date_time_str() + '.mf4',
    'check_msg_delay':          '500',          # [ms] max delay
}


config = {}

needed_msg_id_list = [
        # mandatory msgs
        '0x200',    # BS (Break System) - drive direction, ESP
        '0x300',    # BS - enable ART
        '0x236',    # ART_LRW - Steering
        '0x238',    # ART_MRM - Buttons
        '0x240',    # EZS - Buttons
        '0x212',    # MS - Enable ART
        '0x308',    # MS - Data
        '0x312',    # MS - Moments
        '0x412',    # Kombi - speed
        # other msgs
        '0x408',    # Kombi
        '0x328',    # BS
        '0x218',    # GS - Gearbox System
        '0x418',    # GS
        '0x210',    # MS (Motor System) - Pedal
        '0x608',    # MS
        '0x328',    # BS
    ]

# global storage (dictionary) for CAN Siganls - will be updated with every new msg
vehicle_msg = {'msgs': {}, 'signals': {}}
#{'msgs':{'0x123': 1234567890, '0x234': 1234567891}, 'signals':{ 'Siganl1':12, 'Signal2': 345}}


def main():

    log.info('START')

    mdf = Mdf(config['mdf_log_file'], log)

    #can_0 = Can(config['can_0_interface'], config['can_0_channel'], config['can_0_speed'], config['can_0_dbc'], log)
    can_0 = can.interface.Bus(interface=config['can_0_interface'], channel=config['can_0_channel'], bitrate=500000, app_name='NewApp')

    db_0 = cantools.database.load_file(config['can_0_dbc'])


    #can_0.shutdown_connection()
    #can_0.get_connection()

    #can_1 = Can(config['can_0_interface'], config['can_1_channel'], config['can_0_speed'], config['can_0_dbc'], log)

    ready = False

    #for _ in range(2000):
    while True:
        msg = can_0.recv()

        if msg:
            vehicle_msg_id = hex(msg.arbitration_id)

            # update msg timestamp
            vehicle_msg['msgs'].update({vehicle_msg_id: utils.ts_ms()})


            # decode msg with DBC information to signals
            if vehicle_msg_id in needed_msg_id_list:
                decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

                # store siganls in MDF file
                if config['mdf_log']:
                    mdf.add_signals(decode_msg, signal_prefix='CAN_0_')

                # all signals in the msg
                for key in decode_msg.keys():
                    signal_name = key
                    signal_data = decode_msg[key]

                    # update msg storage
                    vehicle_msg['signals'].update({signal_name: signal_data})

                ready = check.is_acc_ready(vehicle_msg, log)

                if ready:
                    enabled = check.enable_acc(vehicle_msg, log)
                    if enabled:
                        log.info('Enabeled')
                        break
    if config['mdf_log']:
        mdf.write_mdf()

    log.info('READY: ' + str(ready))

    can_0.shutdown()

    print(vehicle_msg)

if __name__ == "__main__":

    try:
        log = Logger('module_name').logger

        log.setLevel(utils.parse_log_level(default_config['loglevel']))
        log.info('Start ' + module_name + ' ' + module_version)

        # load config
        config = Config(module_name, default_config, log).config
        log.debug(config)

        log.setLevel(utils.parse_log_level(config['loglevel']))

        try:
            main()
        except Exception as e:
            log.critical('MAIN CRASH')
            log.error(e)
            traceback.print_exc()

    except Exception as e:
        print('Logger init Error')
        print(e)
        traceback.print_exc()