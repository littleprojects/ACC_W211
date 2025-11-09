
"""
Tool to analyse and manipulate the log raw can log files

File walker to perform some action on the logs
- do correction -> find and correct logging problem in files (for example: change CAN id from INT to HEX)
- tag files with information form the log (max. speed, ART on, limiter on, ...)
- concert logs to mdf...

"""

import glob

from lib import utils
from lib.Logger import Logger

# module name for LOGGING and CONFIG
module_name = 'TOOL_LOG'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.1'

config = {
    'path': '..\..\CAN_Logs',
    'files_search_pattern': '*.log',

    'loglevel': 'INFO',  # debug
}

log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(config['loglevel']))

log.info('Start ' + module_name + ' ' + module_version)

# find all raw CAN log files
search_path = config['path'] + '\\' + config['files_search_pattern']
log.info('Search for: ' + search_path)
log_files = glob.glob(search_path)

log.info('Found ' + str(len(log_files)) + ' files')

log.info(log_files)