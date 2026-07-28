"""
Simple script to REPLAY CAN LOGS from a file back to CAN

Example log data
***<Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>***
10:11:22:5659 Rx 2 0x240 s 8 00 12 00 00 00 00 64 80 
10:11:22:5677 Rx 2 0x230 s 1 08 

- Information lines start and end with ***
- CAN Log have a specefic format
"""

import os
import can
import time
from datetime import datetime
from lib.Config import Config
from lib.Can import Can
from lib import Logger

config = {
    # replay options
    'file': 'can_log_Gratkorn.log',
    'loop': False,     # repeat (1) or stop (0) at the end of a file

    #Todo 'filter': [],       # ignore msg list 

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
        'loglevel': 'DEBUG',
        #'app_name': 'VN1610',  # Hardware interface
        'app_name': 'vCAN',  # virtual CAN interface

        'interface': 'vector',
        'channel': '1',
        'bitrate': '500000',  # 5k baude
        'dbc': 'dbc/CAN_ARS408_id0.dbc', # path to DBC

        'send': True,  # enables or disables MSG sending
    },
    # log
    'loglevel': 'INFO',  # info, debug; with debug also config info will be printed out
    #'loglevel': 'DEBUG',  # info, debug; with debug also config info will be printed out
}

# Init Logger
log = Logger.Log('CAN_REPLAY', log_dir=None).get_logger()
log.setLevel(config['loglevel'])

log.info('Init CAN REPLAY')

config_reader = Config(config)
config = config_reader.config_obj

can0 = Can(config.CAN_0, None)

can0.connect()


def parse_hex(hex_string):
    an_integer = int(hex_string, 16)
    return an_integer # hex()

def timestr2ts(time_string):

    #dt = datetime.strptime(time_string, "%H:%M:%S:%f") # TS befor 1950/1/2 dont work -> python bug
    # workaround
    time_split = time_string.split(':')
    dt = datetime(1970, 1, 2, hour=int(time_split[0]), minute=int(time_split[1]), second=int(time_split[2]), microsecond=int(time_split[3]))

    return dt.timestamp()*1000

def read_line(line):

    """
    example
    ***<Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>***
    10:11:22:5659 Rx 2 0x240 s 8 00 12 00 00 00 00 64 80 
    10:11:22:5677 Rx 2 0x230 s 1 08 
    """

    # skip information lines
    if line.find('*') > -1:
        return None
    
    log.debug(line)

    # split line
    splits = line.split()

    # skip if line is too short or too long
    if len(splits) < 7 or len(splits) > 14:
        return None
    
    ts = timestr2ts(splits[0])

    data = []

    for byte_string in splits[6:]:
        data.append(parse_hex(byte_string))

    log.debug(data)

    msg = {
        'ts': ts,
        'ch': splits[2],
        'id': parse_hex(splits[3]),
        # Todo: type (Standard, extended)
        'dlc': int(splits[5]),
        'data': data
    }

    log.debug(msg)    
    
    try:
        return msg
    except Exception as e:
        log.error(e)
        
    return None
    

    msg = {
        'id': 1,
        'data': []
    }
    #can0.send_message(msg)


def read_file(file):

    dir = os.getcwd()

    file = os.path.normpath(dir + '/' + file)

    log.info('Open file: ' + file)

    if not os.path.exists(file):
        log.error(f"File not found: '{file}' ")
        # deactivate loop
        config['loop'] = 0
        return
    
    line_count = 0
    last_ts = 0

    #try:
    # 'with' Statement stellt sicher, dass die Datei nach dem Block automatisch geschlossen wird,
    # auch wenn Fehler auftreten.
    with open(file, 'r', encoding='utf-8') as datei:
        
        for line in datei:
            # .strip() entfernt führende/nachfolgende Leerzeichen und Zeilenumbrüche (\n, \r, \t)
            line_cleanded = line.strip()

            if line_cleanded: # Nur nicht-leere Zeilen ausgeben
                log.debug(f"Zeile {line_count}: {line_cleanded}")
                
                # parese line
                msg = read_line(line_cleanded)

                #log.debug(msg)
                
                if msg is not None:

                    # if msg['ch'] == '1':
                    can0.send_message(msg)

                    log.debug('Msg sended')

                    new_ts = msg['ts']
                    # delay
                    if last_ts > 0:                        
                        delay_s = (new_ts - last_ts)
                        # cut to long delays
                        if delay_s > 0.005:
                            delay_s = 0.005
                        
                        #log.debug(msg)
                        log.debug('sleep: ' + str(delay_s))
                        time.sleep(delay_s)

                    last_ts = new_ts
                    line_count += 1

                    log.debug('---')

                    # write out a log
                    if line_count == 1 or line_count % 500 == 0:
                        log.info(str(line_count) + ' msg send')

    #except Exception as e:
    #    log.error(e)

    log.info('END FILE')



read_file(config.file)

# loooooooooooop file for eeeeeever
while config.loop:
    log.info('REPEAT FILE')
    read_file(config.file)

log.info('Stop the bus')
can0.shutdown_connection()

log.info('EXIT')