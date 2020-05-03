#!/usr/bin/python3

import sys
import KMControllersS
import motordic

def freeAllMotors():
    motors = motordic.specifySN()
    print(motors)
    for dev in motors.values():
        motor = KMControllersS.USBController(dev)
        motor.free()
        motor.disable()
        print("free " + dev)


if __name__ == '__main__':
    # motors = motordic.specifySN()
    # print(motors)
    # for dev in motors.values():
    #    motor = KMControllersS.USBController(dev)
    #    motor.free()
    #    motor.disable()
    #    print("free " + dev)

    freeAllMotors()
