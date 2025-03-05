"""
Simple scripte to log CAN messages in a file to replay
it at any time with the _can_replay.py script
"""


import can

# Erstelle eine Bus-Instanz
bus = can.interface.Bus(channel='0', interface='vector', bitrate=500000, app_name='NewApp')

i = 0

# Öffne eine Datei zum Speichern der Nachrichten
with open('can_log.asc', 'w') as log_file:

    while True:
        # Empfange Nachrichten und speichere sie in der Datei
        msg = bus.recv()
        if msg:
            log_file.write(f"{msg.timestamp} {msg.arbitration_id:X} {msg.dlc} {' '.join(f'{byte:02X}' for byte in msg.data)}\n")

            i += 1

            if i % 1000 == 0:
                #i = 0
                print(str(i) + ' Msgs recorded')