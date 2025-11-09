	
# PI config

## Hardware
https://www.waveshare.com/wiki/2-CH_CAN_HAT%2B
https://copperhilltech.com/blog/beginners-guide-to-using-socketcan-with-raspberry-pi-and-pican-board/

config
nano /boot/firmware/config.txt

dtparam=spi=on
dtoverlay=i2c0 
dtoverlay=spi1-3cs
dtoverlay=mcp2515,spi1-1,oscillator=16000000,interrupt=22
dtoverlay=mcp2515,spi1-2,oscillator=16000000,interrupt=13

alternative:
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=22
dtoverlay=mcp2515-can1,oscillator=16000000,interrupt=13



## CAN

check
>dmesg | grep spi


-->[    7.388458] mcp251x spi1.2 can0: MCP2515 successfully initialized.
-->[    7.408143] mcp251x spi1.1 can1: MCP2515 successfully initialized.


start CAN
>sudo ip link set can0 up type can bitrate 500000
>sudo ip link set can1 up type can bitrate 500000
>sudo ifconfig can0 txqueuelen 65536
>sudo ifconfig can1 txqueuelen 65536

alternative
> sudo ip link set can0 up type can bitrate 500000
> sudo ip link set can1 up type can bitrate 500000


check with
> ifconfig
or 
> ls /sys/class/net 
or 
> ip link show


stop can
> sudo ifconfig can0 down
> sudo ifconfig can1 down

## Testing

connect CAN0 and CAN1 with to wires.
From H->H and L->L

be sure the 120R termination is set on both CANs

Termina1: Test receive on CAN 0
> candump can0

Terminal2: Test send on CAN 1
> cansend can1 000#11.22.33.44

## Python virtual enviroment

create a new virtual enviroment
> python -m venv ~/can

activate python enviroment
> source can/bin/activate

exit enviroemnt
> deacitvate



### testing with python
in environment

after setting up can 
python -m can.viewer -c can0 -i socketcan

activate python environment
source can/bin/activate

exit environment
deactivate


## AUTOSTART

Service

systemctl 
systemctl status autostart.service

nano /lib/systemd/system/autostart.service

systemctl start autostart.service
start|stop|status

sudo systemctl enable autostart
disable

Serice start the autostart.sh in /home/pi/

## autostart.sh

This script will be start by a service.

- It inits the CAN lines
- starts a Syncthing service to send log data home
- start the can_logger for raw data recording
- start the radar_can_relay to forward speed and yaw to the radar

## log history

- 0-80 raw vehicle can
- 80+ with radar log (first without speed and yaw)
- 100+ CAN_ID hex fix and speed/yaw relay
- 102 swap can lines by wire 1 is not vehicle -> ToDo change in config

