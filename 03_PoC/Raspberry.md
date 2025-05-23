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