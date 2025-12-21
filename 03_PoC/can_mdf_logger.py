
"""
This script log the CAN data and parse it with a CAN Database (DBC) to a MDF file


"""

import can
import cantools
from lib import utils
from lib.Mdf import Mdf
from lib.Logger import Logger


# module name for LOGGING and CONFIG
module_name = 'MDF_LOG'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.2'

config = {
    'loglevel':                 'INFO',             # debug
    #'loglevel':                 'DEBUG',             # debug
    'can_0_dbc':                'dbc/CAN_C.dbc',
    'can_0_dbc':                '../00_Reverseengineering/CAN/CAN_C.dbc',
    'mdf_log_file':             'log/Canlog_' + utils.date_time_str() + '.mf4',
}

log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(config['loglevel']))

log.info('Init')

log.info(('Load DBC: ' + config['can_0_dbc']))
db_0 = cantools.database.load_file(config['can_0_dbc'])

log.info('Logging to: ' + config['mdf_log_file'])
mdf = Mdf(config['mdf_log_file'], log, db_0) #, save_interval=10000)

# Erstelle eine Bus-Instanz
bus = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name='vCAN')

i = 0

log.info('Ready')

# loop infinity
try:
    while True:

        # wait for msgs for 1 sec - is a blocking function
        msg = bus.recv(1)

        if msg:
            vehicle_msg_id = hex(msg.arbitration_id)

            try:
                decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

                mdf.add_signals(decode_msg)

                i += 1
            except:
                pass

            if i == 1:
                log.info('Recording started')

            if i % 1000 == 0:
                log.info('Msgs: ' + str(i))

except KeyboardInterrupt:
    log.info('STOP recording')
    log.info('Shut down bus')
    # stop bus
    bus.shutdown()

    log.info(str(i) + ' Msgs recorded ')

    if i > 0:
        mdf.write_mdf()

    log.info('exit')

