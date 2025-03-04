# Tooling

## CAN interface

To access the CAN Bus of the car is a CAN interface needed.

I choose a Vector VN1610.

Because:
- USB interface
- it comes with two CAN line at one SUBD9 connector
- Good software support (cloud use it with Vector software - but Freeware works also)
- and I had one flying around in my garage
- dont forget to install the driver (XL-Driver Lib)

It only works with CAN Database in the free .dbf format. 
But is also include a hidden converter to create .dbf from .dbc
Tools -> Format Converter -> Other Converters -> DBC to DBF Conversion

## CAN software

**BUSMASTER** is an excelent CAN BUS software. 
- quick to learn
- It helps a lot to read out the CAN and correct the CAN Database

Also ASAMMDF (Python) comes with a good GUI and a loot of tools.

When you install a Vector software. A very usefull comes with it.
**CANdb++** a very intuitive tools to create and mantain CAN Database