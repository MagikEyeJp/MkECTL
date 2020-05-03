#!/usr/bin/python3

import sys
import KMControllersS
import motordic

def preset(id, pos):
    (dev, scale) = motordic.idToDeviceChar(id)
    if len(dev) > 1:
        print('scale:' + str(scale) + ' dev:' + dev)
        motor = KMControllersS.USBController(dev)
        motor.presetPosition(pos * scale)
        print('--preset completed--')
    else:
        print('id not found')


if __name__ == '__main__':
    dev = ''
    args = sys.argv
    if 3 == len(args):
        id = args[1]
        pos = float(args[2])
        preset(id, pos)
    else:
        print('usage :\n preset <motor id(slider ...)> <preset position (mm or deg)>')
