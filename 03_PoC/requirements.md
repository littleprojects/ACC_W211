INIT
* startup
Not Ready (Disabled)
* Ready Checker (No -> Not Ready)
Ready
* Ready Checker (No -> NotReady, Yes -> go on)
* warning calc
* Enable condition (No -> Rady, Yes -> Active)
Activ
* Ready Checker (No -> NotReady, Yes -> go on)
* warning calc
* Diable condition (No -> Active, Yes -> Ready)

Ready_checker
* timeout check: collect all needed CAN messages to fill info storage
    * '0x200',    # BS (Break System) - drive direction, ESP
    * '0x300',    # BS - enable ART
    * '0x236',    # ART_LRW - Steering
    * '0x238',    # ART_MRM - Buttons
    * '0x240',    # EZS - Buttons
    * '0x212',    # MS - Enable ART
    * '0x308',    # MS - Data
    * '0x312',    # MS - Moments
    * '0x412',    # Kombi - speed
* Check Vehicle and Sensor signals
    * no Errors (Vehcile, Radar)
    * other ready conditions (Vehicle, Radar)
    * No Reverse

Enable Condition
* Ready Check ok
* Speed over 30 kph and <180
* Set Speed (Up, Down, resume)

Diable Condition
* cruise control switch push forward
* break manually
* speed is below 30 kph
* Ready Check negativ
* to hard breaking
* to fast steering
* to big Steering angle

Warning calc
* if warnings are active
* distance to low warning <0.8 sec over 3 sec (red distance waring lamp)
* high speed differences to target
