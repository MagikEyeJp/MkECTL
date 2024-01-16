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
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('qtagg')

defaultMotors = {
    "slide": {
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

class KeiganRobot(IRobotController):
    def __init__(self, machineParams=None):
        self.m_machineParams = machineParams
        self.currentMeasureController = None
        self.motorSet = ['slide', 'pan', 'tilt']
        self.settingWindow = None

        # cont
        self.slide = None
        self.pan = None
        self.tilt = None

        self.params = None

    def connect(self):
        global defaultMotors

        if self.m_machineParams is None:
            self.m_machineParams = defaultMotors

        serials = {k: v.get("serial") for k, v in self.m_machineParams.items()}
        scales = {k: v.get("scale") for k, v in self.m_machineParams.items()}
        offsets = {k: v.get("offset") for k, v in self.m_machineParams.items()}

        motordic = {}

        devices = glob.glob(os.path.join('/dev', 'ttyUSB*'))

        for id in serials.keys():
            if serials[id] == "keigan_dummy":
                param = {}
                param['id'] = id
                param['cont'] = KMControllersS_dummy.USBController('dev/dummy')
                param['scale'] = scales[id]
                param['offset'] = offsets[id] if offsets[id] is not None else 0.0
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
                param['offset'] = offsets[id] if offsets[id] is not None else 0.0
                param['SN'] = serialnum
                motordic[id] = param
                motor.set_scaling(scales[id], param['offset'])
            else:
                motor.close()
                motor = None

        self.params = motordic
        # return motordic

    def initialize(self):
        self.slide = self.params.get('slide', {}).get('cont', None)
        self.pan = self.params.get('pan', {}).get('cont', None)
        self.tilt = self.params.get('tilt', {}).get('cont', None)

        if [self.slide, self.pan, self.tilt].count(None) == 0:
            for m in [self.slide, self.pan, self.tilt]:
                self.initializeMotor(m)
            return True
        else:
            return False

    def initializeMotor(self, m: KMControllersS.USBController):
        m.disableCheckSum()
        m.wait_start()      # wait reboot
        m.enable()
        m.interface(8)      # USB only
        m.curveType(1)      # trapezoid speed curve
        m.measureInterval(5)    # 100ms
        m.measureSetting(3)     # measure on
        m.enableMotorMeasurement()  # measure start
        m.targetPos = 0.0

    def initializeOrigins(self, origins=None, callback=None):
        for m in [self.slide, self.pan, self.tilt]:
            m.reboot()
        time.sleep(0.5)

        # slide origin
        GOAL_VELO = 0.1
        GOAL_TIME = 2.0
        m = self.slide
        self.initializeMotor(m)
        speed = 10.0 if self.params.get('slide', {}).get('scale', 1) < 0.0 else -10.0
        m.speed(speed)
        maxTorque = m.read_maxTorque()
        m.maxTorque(1.0)
        m.runForward()
        duration = 0.0
        prev_time = time.time()
        if callback is not None:
            inmain(callback, None, duration, GOAL_TIME)
        time.sleep(0.5)
        while duration < GOAL_TIME:
            (pos, vel, torque) = m.read_motor_measurement()
            if abs(vel) >= GOAL_VELO:
                prev_time = time.time()
            pos_d = {'slide': pos}
            time.sleep(0.2)
            duration = time.time() - prev_time
            inmain(callback, pos_d, duration, GOAL_TIME)
        time.sleep(1.0)
        m.presetPosition(0.0)
        m.free()
        m.maxTorque(maxTorque)

        # pan, tilt origin
        for m in [self.pan, self.tilt]:
            self.initializeMotor(m)


    def changePIDparam(self, pid_category, pid_param, motor_i, value):
        print("changePID", pid_category, pid_param, motor_i, value)
        lpf_index = {'speed': 1, 'qCurrent': 0, 'position': 2}

        if pid_param == 'lowPassFilter':
            self.params[self.motorSet[motor_i]]['cont'].lowPassFilter(lpf_index[pid_category], value)
        elif pid_param == 'posControlThreshold':
            self.params[self.motorSet[motor_i]]['cont'].posControlThreshold(value)
        elif pid_category == 'motion' or pid_category == 'torque':
            execCode = 'self.params[\'%s\'][\'cont\'].%s(%f)' % (self.motorSet[motor_i], pid_param, value)
            print(execCode)
            eval(execCode)
        else:
            execCode = 'self.params[\'%s\'][\'cont\'].%s%s(%f)' % (self.motorSet[motor_i], pid_category, pid_param, value)
            eval(execCode)

    def saveAllRegisters(self):
        for p in self.params.values():
            p['cont'].saveAllRegisters()

    def getPosition(self):
        pos_d = {}
        for k, p in self.params.items():
            pos_d[k] = p['cont'].read_scaled_position()
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

    def moveTo(self, targetPos, wait=False, callback=None, isAborted=None):
        # pos: dict ('slide', 'pan', 'tilt')

        pos_d = {'slide': 0.0, 'pan': 0.0, 'tilt': 0.0}
        vel_d = {'slide': 0.0, 'pan': 0.0, 'tilt': 0.0}
        torque_d = {'slide': 0.0, 'pan': 0.0, 'tilt': 0.0}

        initial_err = 0.0
        minerr = 999999.0  # とりあえず大きい数
        cnt = 0
        GOAL_EPS = 0.003  # FINE目標位置到達誤差しきい値
        NOWAIT_EPS = 0.1  # COARSE目標位置到達誤差しきい値
        GOAL_CNT = 8  # 目標位置到達判定回数

        class Axis:
            def __init__(self, cont, target):
                self.cont = cont
                self.target = target

        def getpos(ax: Axis):
            pos = {}
            for k, v in ax.items():
                pos[k] = v.cont.read_scaled_position()
            return pos

        def geterr(ax: Axis, pos: dict):
            err = 0
            for k, v in ax.items():
                e = (pos[k] - v.target) * v.cont.get_scaling()[0]
                print(f'{k}:{e:.4f}', end=' ')
                err += pow(e, 2)
            return math.sqrt(err)

        axis = {}
        for k, p in self.params.items():
            if k in targetPos:
                c = p['cont']
                c.speed(c.read_maxSpeed())
                c.moveTo_scaled(targetPos[k])
                self.setTargetPosValue(c, c.to_absolute_position(targetPos[k]))     # for PID measurement
                axis[k] = Axis(c, targetPos[k])

        # initial_err = math.sqrt(initial_err)

        pos_d = getpos(axis)
        initial_err = geterr(axis, pos_d)
        if initial_err == 0.0:
            return False

        starttime = time.time()

        while True:
            if isAborted is not None:
                if inmain(isAborted):
                    return True

            @timeout(6)
            def waitmove():
                nonlocal initial_err
                nonlocal minerr
                nonlocal cnt
                nonlocal GOAL_EPS
                nonlocal NOWAIT_EPS
                nonlocal GOAL_CNT

                while True:
                    time.sleep(0.2)
                    errors = 0.0
                    pos_d = getpos(axis)
                    err_pos = geterr(axis, pos_d)
                    print("err=", err_pos, cnt)

                    if callback is not None:
                        inmain(callback, pos_d, initial_err - err_pos, initial_err, time.time() - starttime > 5.0)

                    if err_pos < (GOAL_EPS if wait else NOWAIT_EPS):
                        if wait:
                            cnt += 1
                        else:
                            cnt = GOAL_CNT + 1
                        if cnt > GOAL_CNT:
                            break
                    else:
                        cnt = 0

                    if err_pos < minerr:
                        minerr = err_pos  # 最小値更新
                        break
                return err_pos, pos_d

            try:
                err, pos_d = waitmove()

                if cnt > GOAL_CNT:
                    # raise StopIteration()
                    break

            except TimeoutError:
                print("Timeout")
                return True     # isAborted

        return False

    def setMotorMeasurement(self, enable, motor_i):
        for i, x in enumerate(self.motorSet):
            m = self.params[x]['cont']
            if enable and i == motor_i:
                self.currentMeasureController = m
                self.settingWindow.onChangeTargetPos(m, m.targetPos)
                m.on_motor_measurement_value_cb = self.settingWindow.onMeasure
            else:
                m.on_motor_measurement_value_cb = False
        return self.currentMeasureController

    def setTargetPosValue(self, cont, val):
        cont.targetPos = val
        if cont == self.currentMeasureController:
            self.settingWindow.onChangeTargetPos(cont, val)

    def getSettingWindow(self):
        self.settingWindow = SettingsWindow()
        self.settingWindow.pidChanged.connect(self.changePIDparam)
        self.settingWindow.parameterSaved.connect(self.saveAllRegisters)
        self.settingWindow.graphChanged.connect(self.setMotorMeasurement)
        return self.settingWindow


# ---- Setting Window ----
GRAPH_NUM = 100


class SettingsWindow(QtWidgets.QWidget):
    pidChanged = QtCore.pyqtSignal(str, str, int, float)
    parameterSaved = QtCore.pyqtSignal()
    graphChanged = QtCore.pyqtSignal(bool, int)

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
        self.ui_setting.MotorComboBox.currentIndexChanged.connect(self.changeMotor)

        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.ui_setting.resetButton.setEnabled(False)

        # graph
        self.fig = None
        self.times = []
        self.position = []
        self.position2 = []
        self.velocity = []
        self.torque = []
        self.targetpos = []
        self.starttime = 0
        self.currentTargetPos = 0
        self.currentController = None

    def closeEvent(self, event):
        self.ui_setting.MotorComboBox.setCurrentIndex(0)
        event.accept()

    def onChangeTargetPos(self, cont, val):
        self.currentController = cont
        self.currentTargetPos = cont.to_scaled_position(val)
        print("onChangeTargetPos: ", cont, val)

    def onMeasure(self, pos, velo, trq):
        if self.currentController is not None:
            self.times.append(time.time() - self.start_time)
            self.times.pop(0)
            self.position.append(self.currentController.to_scaled_position(pos))
            self.position.pop(0)
            self.position2.append(self.currentController.to_scaled_position(pos) - self.currentTargetPos)
            self.position2.pop(0)
            self.velocity.append(velo)
            self.velocity.pop(0)
            self.torque.append(trq)
            self.torque.pop(0)
            self.line_pos.set_data(self.times, self.position)
            self.line_pos2.set_data(self.times, self.position2)
            self.line_velo.set_data(self.times, self.velocity)
            self.line_trq.set_data(self.times, self.torque)
            # print(pos, velo, trq)
            plt.xlim(min(self.times), max(self.times))
            self.ax1.set_ylim(min(self.position), max(self.position))
            # self.ax1_2.set_ylim(min(self.position2), max(self.position2))
            self.ax2.set_ylim(min(self.velocity), max(self.velocity))
            self.ax3.set_ylim(min(self.torque), max(self.torque))
            # plt.axis('tight')
            plt.draw()

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
            8: 'position', 9: 'position', 10: 'position', 11: 'position', 12: 'position',
            13: 'motion', 14: 'motion', 15: 'motion',
            16: 'torque', 17: 'torque'
        }
        pid_param_dic = {
            0: 'P', 4: 'P', 8: 'P',
            1: 'I', 5: 'I', 9: 'I',
            2: 'D', 6: 'D', 10: 'D',
            3: 'lowPassFilter', 7: 'lowPassFilter', 11: 'lowPassFilter',
            12: 'posControlThreshold',
            13: 'acc', 14: 'dec', 15: 'maxSpeed',
            16: 'maxTorque', 17: 'limitCurrent'
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
        self.parameterSaved.emit()
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
                },
                'motion': {
                    'acc': [8.0, 3.0, 12.0],
                    'dec': [8.0, 2.0, 4.0],
                    'maxSpeed': [20.0, 5.0, 5.0],
                },
                'torque': {
                    'maxTorque': [5.0, 5.0, 5.0],
                    'limitCurrent': [20.0, 20.0, 20.0],
                }
            }

        self.setDicTable()
        self.ui_setting.resetButton.setEnabled(False)

    def changeMotor(self):
        index = self.ui_setting.MotorComboBox.currentIndex() - 1
        enable = True if index >= 0 else False
        print(enable, index)
        self.start_time = time.time()
        if enable:
            self.makeGraph()
        else:
            self.closeGraph()
        self.graphChanged.emit(enable, index)

    def on_graphClose(event):
        print('Closed Figure!')
        self.graphChanged.emit(False, -1)

    def closeGraph(self):
        plt.close()
        self.fig = None

    def makeGraph(self):
        self.position = [0 for i in range(GRAPH_NUM)]
        self.position2 = [0 for i in range(GRAPH_NUM)]
        self.velocity = [0 for i in range(GRAPH_NUM)]
        self.torque = [0 for i in range(GRAPH_NUM)]
        self.targetpos = [0 for i in range(GRAPH_NUM)]
        self.starttime = time.time()
        self.times = [((GRAPH_NUM - i - 1) * -0.1) for i in range(GRAPH_NUM)]

        if self.fig is None:
            self.fig = plt.figure(figsize=(6, 3))
            win = plt.gcf().canvas.manager.window
            win.setWindowFlags(win.windowFlags() | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowStaysOnTopHint)
            win.setWindowFlags(win.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)
            win.setWindowFlags
            self.ax1 = self.fig.add_subplot(411)
            self.ax1.grid(True)
            self.ax1.set_ylabel('pos (rad)')
            self.ax1_2 = self.fig.add_subplot(412, sharex=self.ax1)
            self.ax1_2.grid(True)
            self.ax1_2.set_ylabel('pos diff (rad)')
            self.ax1_2.set_ylim(-0.5, 0.5)
            self.ax2 = self.fig.add_subplot(413, sharex=self.ax1)
            # ax2.set_ylim(-180, 180)
            self.ax2.grid(True)
            self.ax2.set_ylabel('velo')
            self.ax3 = self.fig.add_subplot(414, sharex=self.ax1)
            # ax3.set_ylim(-180, 180)
            self.ax3.grid(True)
            self.ax3.set_ylabel('trq')

            self.line_pos, = self.ax1.plot(self.times, self.position)
            self.ax1.legend([self.line_pos], ['pos'], loc='upper left')
            self.line_pos2, = self.ax1_2.plot(self.times, self.position2)
            self.ax1_2.legend([self.line_pos2], ['pos_diff'], loc='upper left')
            self.line_velo, = self.ax2.plot(self.times, self.velocity)
            self.ax2.legend([self.line_velo], ['velo'], loc='upper left')
            self.line_trq, = self.ax3.plot(self.times, self.torque)
            self.ax3.legend([self.line_trq], ['trq'], loc='upper left')

            plt.pause(0.001)

