from IRobotController import IRobotController

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
from PyQt5 import QtWidgets, QtCore
import detailedSettings_ui
import json_IO


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

# ---- IMotorRobot Interfaces ----

class KeiganMotorRobot(IRobotController):
    def __init__(self, machineParams=None):
        self.m_machineParams = machineParams
        self.motorSet = ['slider', 'pan', 'tilt']
        self.settingWindow = None

        # cont
        self.slider = None
        self.pan = None
        self.tilt = None

        self.params = None

    def connect(self):
        global defaultMotors

        if self.m_machineParams is None:
            self.m_machineParams = defaultMotors

        serials = {k: v.get("serial") for k, v in self.m_machineParams.items()}
        scales = {k: v.get("scale") for k, v in self.m_machineParams.items()}

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

    def initialize(self):
        self.slider = self.params.get('slider', {}).get('cont', None)
        self.pan = self.params.get('pan', {}).get('cont', None)
        self.tilt = self.params.get('tilt', {}).get('cont', None)

        if [self.slider, self.pan, self.tilt].count(None) == 0:
            for id, p in self.params.items():
                exec('self.%s.enable()' % id)
                exec('self.%s.interface(8)' % id)
                # print(self.slider)

                if "initial_param" in self.m_machineParams[id]:
                    for initKey, initPar in self.m_machineParams[id]["initial_param"].items():
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
            pos_d = {'slider': pos}
            inmain(callback, pos_d, duration, GOAL_TIME)

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

    def getPosition(self):
        pos_d = {}
        vel_d = {}
        torque_d = {}
        for k, p in self.params.items():
            (pos_d[k], vel_d[k], torque_d[k]) = p['cont'].read_motor_measurement()
            pos_d[k] /= p['scale']
        return pos_d

    def presetPosition(self, targetPos):
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
            p['cont'] = None

    def disconnect(self):
        for k, p in self.params.items():
            m = p['cont']
            m.close()
            p['cont'] = None

    def moveTo(self, targetPos, callback, wait=False, isAborted=None, scriptParams=None, mainWindow=None):
        # pos: dict ('slider', 'pan', 'tilt')

        pos_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        vel_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        torque_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}

        initial_err = 0.0
        minerr = 999999.0  # とりあえず大きい数
        cnt = 0
        GOAL_EPS = 0.003  # FINE目標位置到達誤差しきい値
        NOWAIT_EPS = 0.1  # COARSE目標位置到達誤差しきい値
        GOAL_CNT = 8  # 目標位置到達判定回数

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

            @timeout(5)
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

    def getSettingWindow(self):
        self.settingWindow = SettingsWindow()
        self.settingWindow.pidChanged.connect(self.changePIDparam)
        return self.settingWindow


# ---- Setting Window ----

class SettingsWindow(QtWidgets.QWidget):
    pidChanged = QtCore.pyqtSignal(str, str, int, float)

    def __init__(self, parent=None):
        super(SettingsWindow, self).__init__(parent)

        self.ui_setting = detailedSettings_ui.Ui_settings()
        self.ui_setting.setupUi(self)

        self.pidDirPath = 'PIDparams'
        self.savedPIDfile = 'saved_pid.json'

        self.currentPIDvalues = {}
        self.tableWidget = self.ui_setting.pidTable
        self.maxTableHeight = self.tableWidget.maximumHeight()
        self.resetPID()

        self.setDicTable()
        self.tableWidget.cellChanged.connect(self.changeDetailedSettings)
        # self.setTableSize()

        self.defaultWinHeight = self.geometry().height()
        self.defaultTableHeight = self.tableWidget.height()

        self.ui_setting.saveButton.clicked.connect(self.savePID)
        self.ui_setting.resetButton.clicked.connect(self.resetPID)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.ui_setting.resetButton.setEnabled(False)

    def setTableSize(self):

        height = self.defaultTableHeight
        height += self.geometry().height() - self.defaultWinHeight

        posX = self.tableWidget.pos().x()
        posY = self.tableWidget.pos().y()

        # self.tableWidget.setGeometry(posX, posY, width, height)
        if height < self.maxTableHeight:
            self.tableWidget.setFixedHeight(height)
        else:
            self.tableWidget.setFixedHeight(self.maxTableHeight)

    def resizeEvent(self, event):
        print("Detailed Setting resize event")
        self.setTableSize()
        super(SettingsWindow, self).resizeEvent(event)

    def setDicTable(self):
        r = 0
        col = 1

        for i in range(3):
            for pid_category, pid_category_val in self.currentPIDvalues.items():
                for pid_param, pid_param_val in pid_category_val.items():
                    val = self.currentPIDvalues[pid_category][pid_param][i]
                    self.tableWidget.setItem(r, col, QtWidgets.QTableWidgetItem(str(val)))
                    r += 1
            r = 0
            col += 1

    def changeDetailedSettings(self, row, col):
        pid_category_dic = {
            0: 'speed', 1: 'speed', 2: 'speed', 3: 'speed',
            4: 'qCurrent', 5: 'qCurrent', 6: 'qCurrent', 7: 'qCurrent',
            8: 'position', 9: 'position', 10: 'position', 11: 'position', 12: 'position'
        }
        pid_param_dic = {
            0: 'P', 4: 'P', 8: 'P',
            1: 'I', 5: 'I', 9: 'I',
            2: 'D', 6: 'D', 10: 'D',
            3: 'lowPassFilter', 7: 'lowPassFilter', 11: 'lowPassFilter',
            12: 'posControlThreshold'
        }
        print(row, col)
        value = float(self.tableWidget.item(row, col).text())
        self.pidChanged.emit(pid_category_dic[row], pid_param_dic[row], col-1, value)

        self.currentPIDvalues[pid_category_dic[row]][pid_param_dic[row]][col-1] = value
        self.ui_setting.resetButton.setEnabled(True)

    def savePID(self):
        if not os.path.exists(self.pidDirPath):
            os.makedirs(self.pidDirPath)

        json_IO.writeJson(self.currentPIDvalues, self.pidDirPath + '/' + self.savedPIDfile)

        self.ui_setting.resetButton.setEnabled(False)

    def resetPID(self):
        print('resetPID')

        if os.path.exists(self.pidDirPath + '/' + self.savedPIDfile):
            self.currentPIDvalues = json_IO.loadJson(self.pidDirPath + '/' + self.savedPIDfile)
            # print(self.currentPIDvalues)
        else:
            self.currentPIDvalues = {
                'speed': {
                    'P': [14.0, 14.0, 14.0],
                    'I': [0.001, 0.001, 0.001],
                    'D': [0.0, 0.0, 0.0],
                    'lowPassFilter': [0.1, 0.1, 0.1]
                },
                'qCurrent': {
                    'P': [0.2, 0.6, 0.2],
                    'I': [10.0, 4.0, 10.0],
                    'D': [0.0, 0.0, 0.0],
                    'lowPassFilter': [1.0, 1.0, 1.0]
                },
                'position': {
                    'P': [30.0, 80.0, 40.0],
                    'I': [400.0, 20.0, 400.0],
                    'D': [0.0, 0.0, 0.0],
                    'lowPassFilter': [0.1, 0.1, 0.1],
                    'posControlThreshold': [1.0, 1.0, 1.0]
                }
            }

        self.setDicTable()
        self.ui_setting.resetButton.setEnabled(False)




