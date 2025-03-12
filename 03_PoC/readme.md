# Proof of Concept




### Target Selection

The radar return just a list of objects in front of the sensor.
Its our job to select the most relevant object.

A simple way: Just look forward
Closed Object in my driving corridor
|Obj_x| < vehicle_corridor_size_x/2 and min(Obj_y)

For Corners we need to know if we drive on a straight or corner.

Get the corner radius:
R = v/w
v [m/s] (positiv is left rotation)
w [rad/s] (yaw rate)

rad = 1° * Pi/180 = 0,01745 rad

Highway example
v = 100kmh = 27,7ms
w = 2 °/s = 0,0349 ras/s
R = 27,7 / 0,0349 = 793,6  m

City example
V = 30 kph = 8,3 m/s
w = -10 °/s = -0,1745 ras/s
R = 8,3 / -0,1745 = -47,5 m

**Note:**
If w = 0 -> divission by Zero and R is infinite