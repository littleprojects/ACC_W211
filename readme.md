# W211 ACC 

This project is about to replace the ACC (Adaptive Cruise Control) on an MB W211.

Also called ART (AbstandsRegelTempomat) or Distronic.

## Motivation

The w211 radar runs on 24GHz and is disrupted by other radar modern radar systems quite ofter.
The most new car use radar at 24GHz for BlindSpotWarning (BSW).
These systems interfere with the W211 radar and the ACC throws an error and stop working.
In this situation, the ACC/CC cant be used or reactivated for a while. It's impossible to drive with the ACC in traffic anymore.

<img src="00_Reverseengineering/error_msg_4.jpeg">
Error Message

The modern radar uses a frequency sweep. So it changes the frequency permanent to be more robust.


## Limitations

**This is just a Proof of Concept!**

**Don't use this on public road!**

**Don't try this at home.**

**Project is under development**

<hr>

I set this project up in seval steps

## Reverse engineering

This is about to learn how the ACC in the Car works.

**The worst thing first:** The Radar don't have a own compute unit. This is integrated in the ACC control unit.
It's a SCU (Sesor and Control Unit). For this reason, I also need to replace the Sensor and the control unit.

<img src="02_Sensor/Distronic_049.jpg">

The ACC talks with the vehicle about a single CAN line (CAN_C - Engine CAN).
With a CAN Database I can read out all needed information from the vehicle and what is send by the ACC control unit.

Is it possible to replace the ACC with a new controller and sensor?
I think so -> lets try with a Proof of Concept (a simple cruise control at first)

Many thanks to the website:
https://w220.wiki/Distronic#Distronic

And:
https://github.com/rnd-ash/mb-w211-pc

This was a Jumpstart!

Details are here: [Reverse engineering](00_Reverseengineering/readme.md).

## Requirements

Take a look at the [requirements](requirements.md).

Paperwork and math. Here is the magic explaind.
It's the foundation for project.

## Tooling

* USB CAN Interface -> Vector VN1610. Bus other would also work
* CAN logging and interpreting SW -> Busmaster
* small ecu with CAN interface for PoC
  * PI with a CAN hat

<img src="01_Tooling/pi_with_can_hat.jpeg">
Pi with CAN hat for CAN logging and PoC testing
<br>

## Radar Sensor

What radar sensor can replace the original W211 rada.

The **Continental 408-21** looks good. 
- more range than 
- very robust
- easy interface over CAN
- a bit older but not so expensive
- wide short range

<img src="02_Sensor/408.jpeg">
Fits good at the original sensor position.

## Development progress

**Proof of Concept**
- [x] CAR CAN reverse engineering
  - [x] collection raw data for evaluation
- [x] Requirements and engineering – mostly completed
- [x] Simple cruise control to prove the concept – working
- [x] Drinking coffee
- [x] Radar sensor selection
- [x] Radar integration – temporary
  - [x] Target selector – up and running
  
  
**Pilot / Minimum Viable Product** - Bring everything together
- [x] Basic framework (CAN handling)
- [ ] Driver inputs and state machine
- [ ] Radar and tracking module
- [ ] Controller modules
  - [ ] Distance control module (`a_dist`)
  - [ ] Speed control module (`a_speed`)
  - [ ] Warning module
  - [ ] Dynamic limiter module (curve adaptation, `a_max`)
- [ ] Coordinator module `min(a_dist, a_speed, a_max)`
- [ ] Longitudinal control module (vehicle model, `a → M`)
- [ ] Permanent hardware integration
- [ ] ...

<hr>

# Pictures

<img src="02_Sensor/radar_test_setup_2.jpeg"><br>
Temporary radar integration to collect radar data.

<img src="01_Tooling/radar_view_1.jpg"><br>
A live radar object viewer with object filter, target selector and driving path estimation

<img src="00_Reverseengineering/ACC-LIM_statemachine.png"><br>
State machine

<img src="00_Reverseengineering/ACC_Functional_model.png"><br>
Function model

<img src="00_Reverseengineering/ACC_dist_controller.png"><br>
Distance controller model

<hr>

**Credits**

* To the good documentation of the ART/Distronic system
  * https://w220.wiki/Distronic
* CAN Bus data
  * https://github.com/rnd-ash/mb-w211-pc
  * https://github.com/rnd-ash/W203-canbus/tree/master

<hr>

**License**

No License set now. 
So all rights reserved.
Because it is currently under development. 

This project includes third-party libraries.