# PoC on a Raspberry PI

## CAN Board

I the a 2 CAN Channel extention board from waveshare 2-CH CAN HAT+

https://www.waveshare.com/wiki/2-CH_CAN_HAT%2B

* two isolated CAN channels
    * CAN-C
    * Radar CAN
    * optinal with 120R termination - just needed for the radar CAN
* 7-36V DCDC isolated power supply, perfect for automotiv usage
* SPI Interface 
    * CAN controller: MCP2515
    * CAN receiver: SN65HVD230
    * SPI
        * P19 MISO
        * P20 MOSI
        * P21 SCK
        * P17 CS_0
        * P22 INT_0
        * P16 CS_1
        * P13 INT_1

Install lib BCM2835

### Config

> sudo apt update
> sudo apt upgrade

install utils for can commiunication
> sudo apt install can-utils

config
> sudo nano /boot/firmware/config.txt

> dtparam=spi=on
> dtoverlay=i2c0 
> dtoverlay=spi1-3cs
> dtoverlay=mcp2515,spi1-1,oscillator=16000000,interrupt=22
> dtoverlay=mcp2515,spi1-2,oscillator=16000000,interrupt=13
save and exit

reboot to activate
> sudo reboot

check with
> dmesg | grep spi

should report:
> mcp251x spi1.2 can0: MCP2515 successfully initialized.
> mcp251x spi1.1 can1: MCP2515 successfully initialized.
Look good - go ahead

start CAN
> sudo ip link set can0 up type can bitrate 500000
> sudo ip link set can1 up type can bitrate 500000
> sudo ifconfig can0 txqueuelen 65536
> sudo ifconfig can1 txqueuelen 65536

check with
> ifconfig


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

## Python

//> sudo apt install python3-pip

create a virtual environment on pi
> python3 -m venv can

activate it 
> source can/bin/activate

work with python as normal
> pip install can cantools asammdf

## Autostart

Create a service file
>sudo nano /lib/systemd/system/sample.service

with content
>[Unit]
>Description=Autostart Service
>After=multi-user.target
>
>[Service]
>Type=idle
>ExecStart=/home/pi/autostart.sh
>
>[Install]
>WantedBy=multi-user.target

Create an Autosart scrip
>nano /home/pi/autostart.sh

with the content
>#!/bin/bash
>
>echo "yo working"
>
>cd /home/pi
>
>source can/bin/activate
>
>cd /home/pi/ACC_W211/03_PoC
>
>python3 can_logger.py




