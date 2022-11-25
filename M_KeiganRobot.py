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
      "scale": -0.104772141,
      "initial_param": {
        "curveType": 1,
        "maxSpeed": 250,
        "acc": 8,
        "dec": 8,
        "speed": 20,
        "maxTorque": 5
      }
    },
    "pan": {
      "serial": "KM-1S 20BV#3A2",
      "scale": -0.017453293,
      "initial_param": {
        "curveType": 1,
        "maxSpeed": 250,
        "acc": 3,
        "dec": 2,
        "speed": 40,
        "maxTorque": 5
      }
    },
    "tilt": {
      "serial": "KM-1S 0D69#13A",
      "scale": -0.017453293,
      "initial_param": {
        "curveType": 1,
        "maxSpeed": 250,
        "acc": 12,
        "dec": 4,
        "speed": 40,
        "maxTorque": 5
      }
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

    def getMotorDic(self):
        global defaultMotors

        if self.machineParams_m is None:
            self.machineParams_m = defaultMotors

        serials = {k: v.get("serial") for k, v in self.machineParams_m.items()}
        scales = {k: v.get("scale") for k, v in self.machineParams_m.items()}

        motordic = {}

        devices = glob.glob(os.path.join('/dev', 'ttyUSB*'))

        for id in serials.keys():
            if serials[id] == "keigan_dummy":
                param = {}
                param['id'] = id
                param['cont'] = KMControllersS_dummy.USBController('dev/dummy')
                param['scale'] = scales[id]
                param['SN'] = serials[id]
                motordic[id] = param

        for d in devices:
            motor = KMControllersS.USBController(d)
            serialnum = motor.read_SN().decode()  # Serial Number
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
            else:
                motor.close()
                motor = None

        self.params = motordic
        # return motordic

    def initializeMotors(self):
        self.slider = self.params.get('slider', {}).get('cont', None)
        self.pan = self.params.get('pan', {}).get('cont', None)
        self.tilt = self.params.get('tilt', {}).get('cont', None)

        if [self.slider, self.pan, self.tilt].count(None) == 0:
            for id, p in self.params.items():
                exec('self.%s.enable()' % id)
                exec('self.%s.interface(8)' % id)
                # print(self.slider)

                if "initial_param" in self.machineParams_m[id]:
                    for initKey, initPar in self.machineParams_m[id]["initial_param"].items():
                        execCode: str = 'self.%s.%s(%d)' % (id, initKey, initPar)
                        exec(execCode)

                time.sleep(0.2)

            return True
        else:
            return False

    def initializeOrigins(self, origins, callback):
        GOAL_VELO = 0.1
        GOAL_TIME = 2.0
        m = self.slider
        m.speed(10.0)
        m.maxTorque(1.0)
        m.runForward()
        prev_time = time.time()
        duration = 0.0
        while duration < GOAL_TIME:
            time.sleep(0.2)
            (pos, vel, torque) = m.read_motor_measurement()
            if vel >= GOAL_VELO:
                prev_time = time.time()
            duration = time.time() - prev_time
            inmain(callback, {}, duration, GOAL_TIME)

        m.preset_scaled_position(0)
        m.free()
        m.maxTorque(5.0)

    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        lpf_index = {'speed': 1, 'qCurrent': 0, 'position': 2}

        if pid_param == 'lowPassFilter':
            self.params[self.motorSet[motor_i]]['cont'].lowPassFilter(lpf_index[pid_category], value)
        elif pid_param == 'posControlThreshold':
            self.params[self.motorSet[motor_i]]['cont'].posControlThreshold(value)
        else:
            execCode = 'self.params[\'%s\'][\'cont\'].%s%s(%f)' % (self.motorSet[motor_i], pid_category, pid_param, value)
            eval(execCode)

    def getCurrentPos(self):
        pos_d = {}
        vel_d = {}
        torque_d = {}
        for k, p in self.params.items():
            (pos_d[k], vel_d[k], torque_d[k]) = p['cont'].read_motor_measurement()
            pos_d[k] /= p['scale']
        return pos_d

    def presetPos(self, targetPos):
        for k, p in self.params.items():
            if k in targetPos:
                p['cont'].preset_scaled_position(targetPos[k])

    def freeMotors(self):
        for k, p in self.params.items():
            m = p['cont']
            m.free()

    def reboot(self):
        for k, p in self.params.items():
            m = p['cont']
            m.reboot()
            m.close()


    def goToTargetPos(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        # pos: dict ('slider', 'pan', 'tilt')

        pos_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        vel_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        torque_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}

        initial_err = 0.0
        minerr = 999999.0  # とりあえず大きい数
        cnt = 0
        GOAL_EPS = 0.002  # FINE目標位置到達誤差しきい値
        NOWAIT_EPS = 0.1  # COARSE目標位置到達誤差しきい値
        GOAL_CNT = 5  # 目標位置到達判定回数

        for k, p in self.params.items():
            if k in targetPos:
                (init_pos, init_vel, init_torque) = p['cont'].read_motor_measurement()
                initial_err += pow(init_pos - (targetPos[k] * p['scale']), 2)
                p['cont'].moveTo_scaled(targetPos[k])

        initial_err = math.sqrt(initial_err)
        if initial_err == 0.0:
            return False    # isAborted

        # systate.pos = motorPos

        while True:
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
                nonlocal NOWAIT_EPS
                nonlocal GOAL_CNT

                err = 0.0
                while True:


                    time.sleep(0.2)
                    errors = 0.0

                    for k, p in self.params.items():
                        (pos_d[k], vel_d[k], torque_d[k]) = p['cont'].read_motor_measurement()
                        if k in targetPos:
                            errors += pow(pos_d[k] - (targetPos[k] * p['scale']), 2)
                        pos_d[k] /= p['scale']
                    err = math.sqrt(errors)

                        # display Current Pos
                        # mainWindow.motorGUI['currentPosLabel'][motorSet[param_i]].setText('{:.2f}'.format(
                        #     pos[param_i] / scale[param_i]))
                    # yield pos_d
                    inmain(callback, pos_d, initial_err - err, initial_err)

                    if err < (GOAL_EPS if wait else NOWAIT_EPS):
                        print("err=", err)
                        if wait:
                            cnt += 1
                        else:
                            cnt = GOAL_CNT + 1
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

            except TimeoutError:
                return True     # isAborted

        return False




