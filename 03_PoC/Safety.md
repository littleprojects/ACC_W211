# SAFETY

To fullfill safety standards I want to follow the ISO26262.

## ISO 26262

def: Safety -> absence of unreasonable risk
->
def: Functional Safety -> absence of unreasonable risk due hazard caused by malfunctional behavior of E/E-systems
->
def: Malfunctional behavior -> failure or unintended behavior of an item with respect to its design intent
->
def: Hazard: potential source of harm caused by malfunctional behavior
->
def: Hazardous Event: combination of a hazard and an operational situation
->
def: Risk: combination of the probability of the occurance of harm and severity of that harm

## HARA - Hazard analysis and risk assessment 

Method to identify and categorize hazardous events of items and to specify safety goals and ASILs related to the prevention or mitigation of the associated hazards in order to avoid unreasonable risk

* ASIL - Automotive Safety Integrity Level

### Item definition

Item is in this case a ECU how can manupulate. Reduced to the most important points
* acceleration (pedal)
* deceleration (braking)

This are the main function of the system how applicate
* Cruise Control
* Adaptive Cruise Control with Rader sensor
* Speed Limiter

### Situation analysis

Situation we take a close look at
* Parking
* low speed driving
* high speed driving
* cornering

### Determination of hazards

What cloud go wrong?

* Group: "drop out"
    * SW crash
    * connection breaks
    * hardware fails
* unexpected acceleration
* unexpected deceleration

### Determination of hazardous events

Combination of situations and hazards and what could be the result.
Will be done later.

### Clasification of Hazardous events

What hazard events are risk with probability and severity of that harm.
* severity
    * no injuries to "no chance"
* exposure
    * incredible to high probabilbity
* controllability
    * controllable in general to difficult to control or uncontrollable
* System stability

### ASIL determination
Automotive Safety Integrity Level

Result in a rating form A to D for hardware, testing, ... requiremntes
A least stringest level 
D most stringent level -> more safety requirements


### Risk assessment

* Parking
    * drop out -> no risk
    * acceleration -> no risk, car in mostly in P, or controlable with braking
    * deceleration -> no risk
* low speed driving
    * drop out -> no risk, controlable
    * acceleration -> low risk, controlable with braking
    * deceleration -> low risk, controlable with pedal
* high speed driving
    * drop out -> low risk, controlable
    * acceleration -> high risk -> need safety measures
    * decleration -> high risk -> need safety measures 
* cornering
    * drop out -> low risk, controlable
    * accleration -> high risk -> need safety measures
    * deceleration -> high risk -> need safety measures

# Safety Goals

Safety measures to make high risk controlable and to low risk.

Counter measures for unexpected acceleration or deceleration:
* implementing of shutdown / switch off function (braking, Off button, on error detection)
* implementation of overwrite (by pedal) functions
* limitation of the maximal acceleration/deceleration momment
* limitation of the acceleration/deceleration rate

Vehicle:
* if system drops out (no msgs for a short time) ACC will be disabled automatically
* pedel comands (throttle or braking) can overwrite ACC anytime
* Vehcile support with ABS and ESP to make critical situations controlable






