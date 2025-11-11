
"""
Tool to analyse and manipulate the log raw can log files

File walker to perform some action on the logs
- do correction -> find and correct logging problem in files (for example: change CAN id from INT to HEX)
- tag files with information form the log (max. speed, ART on, limiter on, ...)
- concert logs to mdf...

BusMaster Layout
***<Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>***
17:28:32:1449 Rx 1 0x212 s 8 02 A8 27 06 27 06 A7 06

"""

import os
import glob

from lib import utils
from lib.Logger import Logger

# module name for LOGGING and CONFIG
module_name = 'TOOL_LOG'
# just the Version of this script, to display and log; update this at major changes
module_version = '0.0.1'

config = {
    'loglevel': 'INFO',  # debug

    # read files
    'read_path': '../../CAN_Logs',
    #'files_search_pattern': '*.log',   # all files
    'files_search_pattern': 'can_log_[0-8][0-9].log', #'*.log', # first files with Hex error

    # write files
    'write_path': '../../CAN_Logs/new',
    'file_name_prefix': 'new_',


}

log = Logger(module_name).logger
log.setLevel(utils.parse_log_level(config['loglevel']))

log.info('Start ' + module_name + ' ' + module_version)

# find all raw CAN log files
search_path = config['read_path'] + '/' + config['files_search_pattern']
log.info('Search for: ' + search_path)
log_files = glob.glob(search_path)

log.info('Found ' + str(len(log_files)) + ' files')
log.info(log_files)

def parse_line(line):
    # example
    # ***<Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>***
    # 17:28:32:1449 Rx 1 0x212 s 8 02 A8 27 06 27 06 A7 06

    # split by white space
    part = line.split(' ')

    # part[x]
    # 0 time
    # 1 rx tx
    # 2 channel
    # 3 CAN ID
    # ...
    # print(part)

    # quit if line lenght is not in correct range or doesn't have a hex sign
    if len(part) < 7 or len(part) > 14 or part[3].find('0x') < 0:
        # skip further line actions
        # return False
        return line

    # remove line break
    # line = line.replace('\n', '')

    # fix double 0x from bug
    #line = line.replace('0x0x', '0x')

    # remove double line -> main channel was 1
    if part[2] == 'can0':
        return None

    # remove can from channel
    part[2] = part[2].replace('can', '')

    # hex correction int to hex
    can_int_id = int(part[3].replace('0x', ''))
    part[3] = hex(can_int_id)

    # create new line
    new_line = ' '.join(part) # + '\n'

    return new_line

i = 0

# go through the list
for log_file in log_files:

    file_name = os.path.basename(log_file)

    new_file = []

    i += 1

    log.info('Read file: ' + str(i) + '/' + str(len(log_files)) + ' ' + file_name)

    # read file
    #log.info('Open file: ' + file_name)

    with open(log_file, 'r') as file:
        # read line by line
        j = 0
        lines = file.readlines()
        line_count = len(lines)

        for line in lines:
            #print(parse_line(line))

            try:
                new_line = parse_line(line
                if new_line is not None:
                    new_file.append(new_line)
            except:
                pass

            #if new_line is not None:
            #    new_file.append(new_line)

            j += 1

            # percent
            p = j / line_count * 100
            if p % 10 == 0:
                log.info(str(p) + '%')
            #    break

    # write file
    new_log_file = config['write_path'] + '/' + config['file_name_prefix'] + file_name

    log.info('Write to: ' + new_log_file)
    with open(new_log_file, 'w') as file:

        file.write(''.join(new_file))

    # stop after first file
    #break

log.info('Done')
