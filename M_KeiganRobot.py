from IMotorRobot import IMotorRobot

import KMControllersS, KMControllersS_dummy

import os
import glob
import re
import random
import time

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

initialParameters = {
    "slider": {
        "curveType": 1,
        "maxSpeed": 250,
        "acc": 8,
        "dec": 8,
        "speed": 20,
        "maxTorque": 5
    },
    "pan": {
        "curveType": 1,
        "maxSpeed": 250,
        "acc": 3,
        "dec": 2,
        "speed": 40,
        "maxTorque": 5
    },
    "tilt": {
        "curveType": 1,
        "maxSpeed": 250,
        "acc": 12,
        "dec": 4,
        "speed": 40,
        "maxTorque": 5
    }
}

class KeiganMotorRobot(IMotorRobot):
    def __init__(self, machineParams_m=None):
        # super(KeiganMotor, self).__init__(parent)
        self.machineParams_m = machineParams_m

        # cont
        self.slider = None
        self.pan = None
        self.tilt = None

        self.params = None

    def getMotorDic(self):
        global defaultMotors

        if self.machineParams_m is None:
            self.machineParams_m = defaultMotors

        serials = {k: v.get("serial") for k, v in self.machineParams_m.items()}
        scales = {k: v.get("scale") for k, v in self.machineParams_m.items()}

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

        self.params = motordic
        # return motordic

    def initializeMotors(self):
        global initialParameters

        for id, p in self.params.items():
            # motorVal = 'self.' + id
            # locals()[motorVal] = p['cont']
            # locals()[motorVal].enable()
            # locals()[motorVal].interface(8)
            exec('self.%s = p[\'cont\']' % id)
            exec('self.%s.enable()' % id)
            exec('self.%s.interface(8)' % id)
            # print(self.slider)

            for initKey, initPar in initialParameters[id].items():
                execCode: str = 'self.%s.%s(%d)' % (id, initKey, initPar)
                exec(execCode)

            time.sleep(0.2)

# class KeiganMotor(KMControllersS.USBController):
#     def __init__(self, parent=None):
#         super(KeiganMotor, self).__init__(parent)
#         self.interface = 8
#         self.speed = 5
#
#     # def initialize(self):

