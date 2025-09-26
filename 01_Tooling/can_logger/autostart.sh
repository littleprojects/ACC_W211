#!/bin/bash

echo "move old logs"

mv ~/ACC_W211/03_PoC/can_log/*.log ~/Sync/CAN_logs

echo "start Syncthing"

cd ~
syncthing &

echo "setup can"

#ifconfig can0 down
#ip link set can0 type can bitrate 50000
#ifconfig can0 txqueuelen 65536
#ifconfig can0 up

#ifconfig can1 down
#ip link set can1 type can bitrate 50000
#ifconfig can1 txqueuelen 65536
#ifconfig can1 up

sudo ip link set can0 down
sudo ip link set can1 down

sudo ip link set can0 up type can bitrate 500000
sudo ip link set can1 up type can bitrate 500000


echo "load enviroment"

cd /home/pi

source can/bin/activate

echo "Start CAN Logger"

cd /home/pi/ACC_W211/03_PoC

python3 can_logger.py 
