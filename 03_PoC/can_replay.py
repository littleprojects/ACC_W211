"""
Simple script to replay a CAN Log made by can_logger.py
"""

import can
import time

file = 'can_log.asc'

# Erstelle eine Bus-Instanz
bus = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name='NewApp')

speed_factor = 1 # 1 normal, 0,5 half speed, 2 double speed

i = 0

last_ts = 0

print('Replay CAN msg from ' + file)

# Öffne die Datei mit den aufgezeichneten Nachrichten
with open(file, 'r') as log_file:
    print('Start...')
    for line in log_file:
        parts = line.strip().split()
        timestamp = float(parts[0])
        arbitration_id = int(parts[1], 16)
        dlc = int(parts[2])
        data = bytes(int(byte, 16) for byte in parts[3:3 + dlc])

        # Erstelle eine CAN-Nachricht
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)

        # Sende die Nachricht
        bus.send(msg)

        if i > 0:
            # Warte entsprechend der Zeitstempel
            delay = timestamp - last_ts
            time.sleep(delay*speed_factor)
        else:

            time.sleep(0.01)  # first delay

        last_ts = timestamp

        i += 1

        if i % 1000 == 0:
            # i = 0
            print(str(i) + ' Msgs recorded')

    print('END of file')

    bus.shutdown()

    time.sleep(100)