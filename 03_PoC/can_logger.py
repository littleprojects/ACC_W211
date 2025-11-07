"""
Simple scripte to log CAN messages in a file to replay
it at any time with the BusMaster

BusMaster Layout
***<Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>***
17:28:32:1449 Rx 1 0x212 s 8 02 A8 27 06 27 06 A7 06
"""

import os
import can
import time
import datetime

from lib.Storage import Storage

print('sleep a bit')

# sleep a while, so the  system can start up correctly
time.sleep(10)


def date_time_str(ts=time.time()):
    try:
        return str(datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y %H:%:M%S.%f')[:-3])
    except:
        print('DATETIME ERROR')
        return str('2025-09-05 01:02:03.4')


def time_str(ts=time.time()):
    return str(datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S:%f')[:-2])


def log_string(msg):
    # example string
    # 17:28:32:1469 Rx 1 0x308 s 8 80 02 A5 00 00 78 A7 38
    log = time_str(time.time())
    log += ' Rx'
    log += ' ' + msg.channel
    log += ' 0x' + str(msg.arbitration_id)
    if msg.is_remote_frame:
        log += ' x '
    else:
        log += ' s '
    log += str(msg.dlc) + ' '
    log += ' '.join(f'{byte:02X}' for byte in msg.data)
    log += '\n'

    # log_file.write(f"{msg.timestamp} {msg.arbitration_id:X} {msg.dlc} {' '.join(f'{byte:02X}' for byte in msg.data)}\n")

    return log

print('Start CAN Logger')

file_name = 'can_log/can_log_'  # + Counter I
file_type = '.log'

# init dataset
data = {'i': 0}

# loads setting from file
store = Storage('can_logger_storage.sav', data)
i = store.data['i']
store.data['i'] += 1
store.write()

file = file_name + str(i) + file_type

# create folder to file
os.makedirs(os.path.dirname(file), exist_ok=True)

print('log to: ' + file)

# init can
#print('CAN setup')
#os.system('sudo ifconfig can0 down')
#os.system('sudo ip link set can0 type can bitrate 50000')
#os.system('sudo ifconfig can0 txqueuelen 65536')
#os.system('sudo ifconfig can0 up')

#os.system('sudo ifconfig can1 down')
#os.system('sudo ip link set can1 type can bitrate 50000')
#os.system('sudo ifconfig can1 txqueuelen 65536')
#os.system('sudo ifconfig can1 up')

print('CAN connect')

# connect to can
bus0 = can.interface.Bus(channel='can0', interface='socketcan', bitrate=500000)
bus1 = can.interface.Bus(channel='can1', interface='socketcan', bitrate=500000)

i = 1
j = 1

# Öffne eine Datei zum Speichern der Nachrichten
with open(file, 'w') as log_file:
    # header
    try:
        print('write header')
        log_file.write('''***BUSMASTER Ver 3.2.2***
***PROTOCOL CAN***
***NOTE: PLEASE DO NOT EDIT THIS DOCUMENT***
***[START LOGGING SESSION]***
***START DATE AND TIME ''' + date_time_str() + '''***
***HEX***
***SYSTEM MODE***
***START CHANNEL BAUD RATE***
***CHANNEL 1 - Vector - VN1610 Channel 1 SN - 553 - 500000 bps***
***END CHANNEL BAUD RATE***
***START DATABASE FILES***
***END DATABASE FILES***
***<Time><Tx/Rx><Channel><CAN ID><Type><DLC><DataBytes>***

''')
    except:
        print('CANT WRITE HEADER')

print('wait for CAN frames')

# loooooooooooooooooooooooooooop
try:
    while True:
        # can receive and write to file
        msg0 = bus0.recv(0.001)
        msg1 = bus1.recv(0.001)

        if msg0 or msg1:
            with open(file, 'a') as log_file:
                if msg0:
                    log_file.write(log_string(msg0))
                    i += 1

                if msg1:
                    log_file.write(log_string(msg1))
                    i += 1

        # idle counter
        j += 1

        if i > 1000:
            print('' + str(i) + ' Msgs recorded')
            i = 1
            j = 1

        if j > 20000:
            i = 1
            print('waiting')
except KeyboardInterrupt:
    print('shutdown bus')
    bus0.shutdown()
    bus1.shutdown()

print('EXIT')
