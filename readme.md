# W211 ACC

This project is about to replace the ACC radar a MB W211.

The radar runs on 24GHz and is disrupted by other radar systems.
The most new car use radar at 24GHz for BlindSpotWarning (BSW).
This systems interfier with the W211 radar and the ACC thors an error and stop working.

I set this porjevt up in seval steps

## Reverseengieeing

This is about to learn how the ACC in the Car works.

Write down the basic functions and technical details how the ACC in the Car works.

The ACC talks with the vehicle about a single CAN line (CAN_C - Engine CAN).
With a Database I can read out all needed information how sends the vehicle and the ACC.

Is it possible to replace the ACC with a new controller and sensor?
I think so -> lets try with a Proofe of Concept (a simple cruise controll at first)

Many thanks to the website:
https://w220.wiki/Distronic#Distronic

And:
https://github.com/rnd-ash/mb-w211-pc

This was a Jumpstart!

## Tooling

Note about the Tooling in need to do this.

## Radar Sensor

What radar sensor can replace the original W211 rada.

The **Continental 408-21** looks good. 
- more range than 
- very robust
- easy interface over CAN
- little bit older but not so expensiv
- wide short range

## PoC

In Progress