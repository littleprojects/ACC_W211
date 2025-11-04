# Requiremnts

Limiter and ACC are controlled by the ACC ecu program.

# ACC

## State machine

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

## Input

# Ready_checker
* timeout check: collect all NEEDED CAN messages to fill info storage
    * '0x200',    # BS (Break System) - drive direction, ESP
    * '0x300',    # BS - enable ART
    * '0x236',    # ART_LRW - Steering
    * '0x238',    # ART_MRM - Buttons
    * '0x240',    # EZS - Buttons
    * '0x212',    # MS - Enable ART
    * '0x308',    # MS - Data
    * '0x312',    # MS - Moments
    * '0x412',    # Kombi - speed
* No NEEDED CAN msg is older than 500ms
* Check Vehicle and Sensor signals
  * **CANCEL/DISABLE** Conditions
    * Errors (Vehicle, Radar)
      * ESP_KL = 1 (ESP Light ON)
      * ESP_INFO_DL = 1 (ESP Info Light ON)
      * ESP_INFO_BL = 1 (ESP Info Light Blinking is ON)
      * ABS_KL = 1 (ABS)
      * BRE_KL = 1 (Break)
      * NOTL = 1 (Engine Error - Notlauf)
      * OEL_KL = 1 (Oil warning)
      * UEHITZ = 1 Over heating
      * TEMP_KL = 1 water overheating
    * other ready conditions (Vehicle, Radar)
      * ART_E = 0 (ART not Enabeld)
      * ART_VH = 0 (ART not registered)
    * No Reverse
      * WHST != 4 (Whalhebelstellung is not D)
      * DRTGTM = 2 (Driving direction reverse)

### Enable Condition
* Ready Check ok
* Speed over 30 kph and <180
* Set Speed (Up, Down, resume)

### Diable Condition
* cruise control switch push forward
* break manually
* speed is below 30 kph
* Ready Check negativ
* to hard breaking
* to fast steering
* to big Steering angle

### Warning calc
* if warnings are active
* distance to low warning <0.8 sec over 3 sec (red distance waring lamp)
* high speed differences to target


if distance_to_vehicle <= warn_dist(speed_kph) for 3 sec and warning_tone_active:
  send warning  

Note: distances below 0.5 sec is punishable. This are 9 Meter a 50kph or 18m at 100hph

## Ouput

### CAN Msg

ART 0x250

| Signal    | Unit     | Description                    | Relation                         | 
|-----------|----------|--------------------------------|----------------------------------|
| DYN_UNT   | [on/off] | ?                              | ?                                |
| BL_UNT    | [on/off] | (No breaklight a low breaking) | active if breaking <0,3m/s²      |             
| ART_BRE   | [on/off] | (ART breaks)                   | decelleration needed             |           
| ART_OK    | [on/off] | ART ok                         | Status OK                        |         
| SLV_ART   | [?]      | (Gearshift adapation)          | ?                                |  
| CAS_REG   | [on/off] | (City assist active)           |                                  |     
| NDYN_ART  | [on/off] | dynamik moment request         | ?                                |   
| MPAR_ART  | [on/off] | pariaty                        | changes a moment request updates | 
| ART_REG   | [on/off] | ART active                     | ART do the magic                 |
| LIM_REG   | [on/off] | Limiter active                 | 
| M_ART     | [Nm]     | Acceleration moment request    | for acceleration                 |
| MBRE_ART  | [Nm]     | deccelration moment requst     | for decceleration                | 
| GMIN_ART  | [gear]   | min gear                       |
| GMIN_ART  | [gear]   | max gear                       |
| AKT_R_ART | [on/off] | downshift request              |

ART 0x258

| Signal         | Unit       | Description                                 | Relation                                                  | 
|----------------|------------|---------------------------------------------|-----------------------------------------------------------|
| ART_ERROR      | [enum]     | Error code                                  | 4 External Error                                          |
| ART_INFO       | [on/off]   | Info light                                  | At warnings                                               |
| ART_WT         | [on/off]   | Warning sound                               | At warnings                                               |
| S_OBJ          | [on/off]   | standing object detected                    | ?                                                         |
| ART_DSPL_EIN   | [on/off]   | show ART display                            | at activation and warnings                                |
| V_ART          | [kph]      | set ART Speed                               | for segment display                                       |
| ABST_R_OBJ     | [m]        | distance to relevant object                 | Dspl info                                                 |
| SOLL_ABST      | [m]        | set min distance                            | Dspl info                                                 | 
| TEM_EIN_ART    | [on/off]   | ART speed control active                    | Cruise controll ready                                     |
| ART_DSPL_BL    | [on/off]   | Speed display blinking                      | ?                                                         |
| ART_SEG_EIN    | [on/off]   | show ART speed segments on display          | = ART_EIN (if SGT_VH)                                     |
| OBJ_ERK        | [on/off]   | object detected                             | show car on display with ABST_R_OBJ                       |
| ART_EIN        | [on/off]   | ART is on                                   | 1 if ART is available                                     | 
| ART_DSPL_LIM   | [on/off]   | display "---"                               | if vehicle is to slow or fast                             |
| ART_VFBR       | [on/off]   | Display ART off (0)                         | ?                                                         |
| ART_DSPL_PGB   | [on/off]   | show "winter tyer limit reached"            | ...                                                       |
| V_ZIEL         | [kph]      | speed of target vehicle                     | Dspl on segemnt tacho settet speed                        |
| ASSIST_FKT_AKT | ?          | aktive function                             | ? always 0                                                | 
| AAS_LED_BL     | [on/off]   | blink distance assist LED                   | ? always 0                                                |
| ObJ_AGB        | [on/off]   |  Object offer distance assist               | ? always 0                                                |
| ART_ABW_AKT    | [on/off]   | ART distance warning is active              | will be switched by ART_ABW_BET                           |
| ART_REAKT      | [on/off]   | display "reaktivation after error possible" | ? reaktivation after error "overheat"                     |
| ART_UEBERSP    | [on/off]   | ART overwriten by driver "ART passiv"       | M_FV > M_ART                                              | 
| ART_DSPL_NEU   | [on/off]   | reset display time                          | at ART activation, cut out, low speed >30, V_Ziel changes |  
| ASSIST_ANZ_V2  | ?          | Assistsystem display requerst               | ? always 0                                                |
| CAS_ERR_ANZ    | ?          | CAS (city assist system) display request    | ?                                                         | 


### Distance Calc

SOLL_ABSTAND is linked to Speed (kph) and ART_ABSTAND (0-200)

ART_ABSTAND
200 = short
100 = normal
0 = wide

min distance 3.5m

factor_var = ART_ABSTAND / -100 # turn 200->-2; 100->-1; 0->0
SOLL_ABSTAND [m] = round(Speed * (0,475 - factor_var * 0,2476 ) + 3.5) 

Or a 3D Look Up Table

Warn if distance below 0.8 sec
```
# return the distance of 0.8 sec
warn_dist (speed):
  return speed * 0.36 * 0.8
```


## Limiter

* limit speed to target speed
* ajust speed limit +1, +10 or -10 kph
* diable with button
* diable at kick down

