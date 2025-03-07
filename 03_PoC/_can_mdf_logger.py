
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
module_version = '0.0.1'

config = {
    #'loglevel':                 'INFO',             # debug
    'loglevel':                 'DEBUG',             # debug
    'can_0_dbc':                'CAN_C.dbc',
    'mdf_log_file':             'log/Canlog_' + utils.date_time_str() + '.mf4',
}

log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(config['loglevel']))

db_0 = cantools.database.load_file(config['can_0_dbc'])

mdf = Mdf(config['mdf_log_file'], log, db_0)

# Erstelle eine Bus-Instanz
bus = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name='NewApp')

i = 0

log.info('Start Logging to: ' + config['can_0_dbc'])

# loop infinity
while True:

    msg = bus.recv()

    if msg:
        vehicle_msg_id = hex(msg.arbitration_id)

        try:
            decode_msg = db_0.decode_message(msg.arbitration_id, msg.data)

            mdf.add_signals(decode_msg)

            i += 1
        except:
            pass

        if i % 1000 == 0:
            log.info('Msgs: ' + str(i))
