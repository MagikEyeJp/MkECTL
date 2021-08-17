from IMotorRobot import IMotorRobot

import KMControllersS, KMControllersS_dummy

import os
import glob
import re
import random
import time
import math
from timeout_decorator import timeout, TimeoutError
import numpy as np
from qtutils import inmain


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

        self.motorSet = ['slider', 'pan', 'tilt']

        # cont
        self.slider = None
        self.pan = None
        self.tilt = None

        self.params = None

        self.pid_settings = {
            'speed': {
                'P': [14.0, 14.0, 14.0],
                'I': [0.001, 0.001, 0.001],
                'D': [0.0, 0.0, 0.0]
            },
            'position': {
                'P': [30.0, 80.0, 40.0],
                'I': [400.0, 20.0, 400.0],
                'D': [0.0, 0.0, 0.0]
            },
            'qCurrent': {
                'P': [0.2, 0.6, 0.2],
                'I': [10.0, 4.0, 10.0],
                'D': [0.0, 0.0, 0.0]
            }
        }

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

        self.slider = self.params.get('slider', {}).get('cont', None)
        self.pan = self.params.get('pan', {}).get('cont', None)
        self.tilt = self.params.get('tilt', {}).get('cont', None)

        if [self.slider, self.pan, self.tilt].count(None) == 0:
        # try:
            for id, p in self.params.items():
                # exec('self.%s = p[\'cont\']' % id)
                exec('self.%s.enable()' % id)
                exec('self.%s.interface(8)' % id)
                # print(self.slider)

                for initKey, initPar in initialParameters[id].items():
                    execCode: str = 'self.%s.%s(%d)' % (id, initKey, initPar)
                    exec(execCode)

                time.sleep(0.2)

            return True
        else:
        # except Exception:
            return False

    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        execCode = 'self.params[\'%s\'][\'cont\'].%s%s(%f)' % (self.motorSet[motor_i], pid_category, pid_param, value)
        val = eval(execCode)

        self.pid_settings[pid_category][pid_param][motor_i] = value
        print(self.pid_settings)

    def goToTargetPos(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        # pos: dict ('slider', 'pan', 'tilt')

        pos_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        vel_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        torque_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}

        initial_err = 0.0
        minerr = 999999.0  # とりあえず大きい数
        cnt = 0
        GOAL_EPS = 0.002  # 目標位置到達誤差しきい値
        GOAL_CNT = 5  # 目標位置到達判定回数

        for id, p in self.params.items():
            if targetPos[id] != None:
                (init_pos, init_vel, init_torque) = p['cont'].read_motor_measurement()
                initial_err += pow(init_pos - (targetPos[id] * p['scale']), 2)

                p['cont'].moveTo_scaled(targetPos[id])

        initial_err = math.sqrt(initial_err)
        if initial_err == 0.0:
            return False    # isAborted

        # systate.pos = motorPos

        if wait:
            while True:
                # if isAborted(scriptParams, mainWindow):
                #     return mainWindow.stopClicked
                if isAborted is not None:
                    stopClicked = inmain(isAborted, scriptParams, mainWindow)
                    if stopClicked:
                        return stopClicked

                @timeout(8)
                def waitmove():
                    nonlocal initial_err
                    nonlocal minerr
                    nonlocal cnt
                    nonlocal GOAL_EPS
                    nonlocal GOAL_CNT

                    err = 0.0
                    while True:


                        time.sleep(0.2)
                        errors = 0.0

                        for id, p in self.params.items():
                            if targetPos[id] != None:
                                (pos_d[id], vel_d[id], torque_d[id]) = p['cont'].read_motor_measurement()
                                errors += pow(pos_d[id] - (targetPos[id] * p['scale']), 2)
                                pos_d[id] /= p['scale']
                        err = math.sqrt(errors)

                            # display Current Pos
                            # mainWindow.motorGUI['currentPosLabel'][motorSet[param_i]].setText('{:.2f}'.format(
                            #     pos[param_i] / scale[param_i]))
                        # yield pos_d
                        inmain(callback, pos_d, initial_err, err)

                        if err < GOAL_EPS:
                            print("err=", err)
                            cnt += 1
                            if cnt > GOAL_CNT:
                                break
                        else:
                            cnt = 0

                        if err < minerr:
                            # print("err=", err)
                            minerr = err  # 最小値更新
                            break
                    return err, pos_d

                try:
                    err, pos_d = waitmove()
                    print("err=", err)
                    # yield pos_d

                    if cnt > GOAL_CNT:
                        # raise StopIteration()
                        break

                    # if isAborted is None:   # main window event
                    #     return True # isFinished
                    # else:   # script event
                    #     return False    # isStopped

                except TimeoutError:
                    # if isAborted is None:   # main window event
                    #     return False # isFinished
                    # else:   # script event
                    #     return True    # isStopped
                    return True     # isAborted
            return False

        else:
            @timeout(8)
            def calc_err():
                nonlocal initial_err

                while True:
                    time.sleep(0.2)
                    errors = 0.0

                    for id, p in self.params.items():
                        if targetPos[id] != None:
                            (pos_d[id], vel_d[id], torque_d[id]) = p['cont'].read_motor_measurement()
                            errors += pow(pos_d[id] - (targetPos[id] * p['scale']), 2)
                            pos_d[id] /= p['scale']
                    err = math.sqrt(errors)

                    inmain(callback, pos_d, initial_err, err)

                    if err < 0.05:
                        # minerr = err  # 最小値更新
                        break
                # return err

            try:
                calc_err()
            except TimeoutError:
                return True

            return False

# class KeiganMotor(KMControllersS.USBController):
#     def __init__(self, parent=None):
#         super(KeiganMotor, self).__init__(parent)
#         self.interface = 8
#         self.speed = 5
#
#     # def initialize(self):

