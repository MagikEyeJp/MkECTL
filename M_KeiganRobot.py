from IMotorRobot import IMotorRobot

import KMControllersS, KMControllersS_dummy

import os
import glob
import re
import random

defaultMotors = {
    "slider": {
      "serial": "KM-1U 9PIG#CD1",
      "scale": -0.104772141
    },
    "pan": {
      "serial": "KM-1S 20BV#3A2",
      "scale": -0.017453293
    },
    "tilt": {
      "serial": "KM-1S 0D69#13A",
      "scale": -0.017453293
    }
}

class KeiganMotorRobot(IMotorRobot):
    def __init__(self):
        # super(KeiganMotor, self).__init__(parent)
        self.slider = None

    def getMotorDic(self, motors=None):
        if motors is None:
            motors = defaultMotors

        serials = {k: v.get("serial") for k, v in motors.items()}
        scales = {k: v.get("scale") for k, v in motors.items()}

        motordic = {}
        calib_flag: bool = True

        devices = glob.glob(os.path.join('/dev', 'ttyUSB*'))
        if re.search('.+_dummy', random.choice(list(serials.values()))):  # dummy  devices: dictionary
            devices = ['slider', 'pan', 'tilt']  # pseudo port name = id
            calib_flag = False
            print("dummy mode.")
        else:  # real calibration
            pass

        for d in devices:
            if calib_flag == True:  # real calibration or test one
                motor = KMControllersS.USBController(d)
                serialnum = motor.read_SN().decode()  # Serial Number
                print(d, serialnum)
            else:  # dummy
                motor = KMControllersS_dummy.USBController(d)
                serialnum = serials[d]
                print(d, serialnum)

            if serialnum in serials.values():
                id = {v: k for k, v in serials.items()}[serialnum]  # https://note.nkmk.me/python-dict-swap-key-value/
                param = {}
                param['id'] = id
                param['cont'] = motor
                param['scale'] = scales[id]
                param['SN'] = serialnum
                motordic[id] = param

                motor.set_scaling(scales[id], 0.0)  # offset = 0.0 (temp)

        return motordic
