#!/usr/bin/env python3
# coding: utf-8

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys
import time
import os
import re
from functools import partial
import datetime
from playsound import playsound
import json
import subprocess

import MyDoubleSpinBox
from M_KeiganRobot import KeiganMotorRobot
import mainwindow_ui
import execute_script
import sensors
import detailedSettings_ui
import ini
import json_IO
from UIState import UIState
from SensorInfo import SensorInfo

import IRLightMkE
import IRLightPapouch
import IRLightNumato
import IRLightDummy
from IMainUI import IMainUI


class ScriptParams():
    def __init__(self):
        self.now = datetime.datetime.now()

        self.scriptName: str = ''
        self.commandNum: int = 0
        self.baseFolderName: str = 'data'
        self.subFolderName: str = self.now.strftime('%Y%m%d_%H%M%S')
        self.isContinue = False
        self.start_command_num: int = 0

        self.IRonMultiplier = 1.0
        self.IRoffMultiplier = 1.0
        self.isoValue = '(DEFAULT)'

    def renewSubFolderName(self):
        self.now = datetime.datetime.now()
        self.subFolderName = self.now.strftime('%Y%m%d_%H%M%S')

class MyMessageBox(QtWidgets.QMessageBox):
    def __init__(self):
        super(MyMessageBox, self).__init__()

    def closeEvent(self, event: QtGui.QCloseEvent):  # real signature unknown; restored from __doc__
        """ closeEvent(self, QCloseEvent) """
        answer = QtWidgets.QMessageBox.question(
            self,
            'Message',
            'Are you sure you want to quit ?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No)
        if answer == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

class DetailedSettingsWindow(QtWidgets.QWidget):
    pidChanged = QtCore.pyqtSignal(str, str, int, float)

    def __init__(self, parent=None, mainUI:IMainUI=None):
        super(DetailedSettingsWindow, self).__init__(parent)
        # self.pidChanged.connect(self.mainUI.motorRobot.changePIDparam)
        self.mainUI = mainUI

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
        super(DetailedSettingsWindow, self).resizeEvent(event)

    def setDicTable(self):
        r = 0
        col = 1

        for i in range(len(self.mainUI.motorRobot.params.keys())):
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

class Ui(QtWidgets.QMainWindow, IMainUI):
    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.ui = mainwindow_ui.Ui_mainwindow()
        self.ui.setupUi(self)
        self.setStyleSheet("QMainWindow::separator{ background: darkgray; width: 1px; height: 1px; }")
        self.scriptParams = ScriptParams()

        # self.subWindow = sensors.SensorWindow(mainUI=self)

        ### docking window https://www.tutorialspoint.com/pyqt/pyqt_qdockwidget.htm
        self.subWindow = sensors.SensorWindow(mainUI=self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.subWindow)
        self.sensorWinWidth = self.subWindow.frameGeometry().width()
        self.sensorWinHeight = self.subWindow.frameGeometry().height()
        self.subWindow_isOpen = False

        ### detailed settings window
        self.detailedSettingsWindow = None  # made in initializeMotors()

        self.ui.Settings.hide()

        self.initializeProcessFlag = False
        self.ui.Settings.hide()

        self.ui.manualOperation.setEnabled(False)
        self.ui.SectionIRlightControl.setEnabled(False)
        self.ui.continueButton.setEnabled(False)
        self.ui.executeScript_button.setEnabled(False)
        self.ui.progressBar.setEnabled(False)

        # config file
        self.configIniFile = 'data/MkECTL.ini'

        # IR light
        self.isPortOpen = True
        self.IRport = None
        self.IRLight = None
        # self.openIR('/dev/ttyACM0')

        # scripting
        self.done = 0
        self.total = 0
        self.percent = 0
        self.stopClicked = False
        self.demo_script = 'script/demo.txt'

        self.updateScriptProgress()
        self.ui.progressBar.setValue(self.percent)
        self.ui.stopButton.clicked.connect(self.interrupt)

        # 画面サイズを取得 (a.desktop()は QtWidgets.QDesktopWidget )  https://ja.stackoverflow.com/questions/44060/pyqt5%E3%81%A7%E3%82%A6%E3%82%A3%E3%83%B3%E3%83%89%E3%82%A6%E3%82%92%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%81%AE%E4%B8%AD%E5%A4%AE%E3%81%AB%E8%A1%A8%E7%A4%BA%E3%81%97%E3%81%9F%E3%81%84
        a = QtWidgets.qApp
        desktop = a.desktop()
        self.geometry = desktop.screenGeometry()
        # ウインドウサイズ(枠込)を取得
        self.framesize = self.frameSize()
        # ウインドウの位置を指定
        # self.move(geometry.width() / 2 - framesize.width() / 2, geometry.height() / 2 - framesize.height() / 2)
        self.move(int(self.geometry.width() / 2 - self.framesize.width() / 2),
                  int(self.geometry.height() / 2 - self.framesize.height() / 2))
        self.maxWinWidth = self.size().width()
        self.maxWinHeight = self.size().height()
        self.isMaxWinSize = False

        # motor
        self.motorSet = ['slider', 'pan', 'tilt']
        self.motorRobot = None  # instance of M_KeiganRobot
        self.motorGUI: dict = {}  # 'exe', 'posSpin', 'speedSpin', 'currentPosLabel'  # GUI objects related to motors  # Dict of dictionaries

        self.states = set()

        self.devices: dict = {}  # 'motors', 'robot', 'lights', '3Dsensors' etc.  # Dict of dictionaries

        if not os.path.exists(self.scriptParams.baseFolderName):
            os.makedirs(self.scriptParams.baseFolderName)

        self.devices['3Dsensors'] = self.subWindow

        self.make_motorGUI()

        # motor-related process
        for m_name in self.motorSet:
            exeButtonName: str = self.motorGUI['exe'][m_name].objectName()
            speedSpinName: str = self.motorGUI['speedSpin'][m_name].objectName()
            # print(m_name, exeButtonName)

            # exe buttons
            self.motorGUI['exe'][m_name].clicked.connect(partial(lambda o: o.determine(), self.motorGUI['posSpin'][m_name]))
            # position spinboxes
            self.motorGUI['posSpin'][m_name].valueChanged.connect(self.judgePresetEnable)
            self.motorGUI['posSpin'][m_name].valueDetermined.connect(partial(lambda n: self.exeButtonClicked(n), exeButtonName))
            # speed spinboxes
            self.motorGUI['speedSpin'][m_name].valueChanged.connect(partial(lambda n: self.updateSpeed(n), speedSpinName))
            # https://melpon.hatenadiary.org/entry/20121206/1354636589

        self.ui.rebootButton.clicked.connect(self.rebootButtonClicked)

        # other buttons
        self.ui.initializeButton.setEnabled(False)
        self.ui.initializeButton.clicked.connect(self.initializeMotors)
        self.ui.MagikEye.clicked.connect(lambda: self.demo(False))
        self.ui.getCurrentPosButton.setEnabled(False)
        self.ui.getCurrentPosButton.clicked.connect(self.getCurrentPos)
        self.ui.selectScript_toolButton.clicked.connect(self.openScriptFile)
        self.ui.selectBaseFolder_toolButton.clicked.connect(self.openBaseFolder)
        self.ui.selectSubFolder_toolButton.clicked.connect(self.openSubFolder)
        self.ui.renewSubFolder_toolButton.clicked.connect(self.renewSubFolder)
        self.ui.executeScript_button.clicked.connect(lambda: self.run_script(False))
        self.ui.continueButton.clicked.connect(lambda: self.run_script(True))
        self.ui.viewSensorWinButton.clicked.connect(lambda: self.showSubWindow(self.geometry, self.framesize))
        self.ui.sliderOriginButton.clicked.connect(self.initSliderOrigin)
        self.ui.freeButton.clicked.connect(self.freeAllMotors)
        self.ui.onL1Button.clicked.connect(lambda: self.IRlightControl(1, True))
        self.ui.offL1Button.clicked.connect(lambda: self.IRlightControl(1, False))
        self.ui.onL2Button.clicked.connect(lambda: self.IRlightControl(2, True))
        self.ui.offL2Button.clicked.connect(lambda: self.IRlightControl(2, False))
        self.ui.setAsHomeButton.clicked.connect(self.setHome)
        self.ui.goHomeButton.clicked.connect(self.goToHomePosition)
        self.ui.saveButton.clicked.connect(self.savePositions)
        self.ui.GoButton.clicked.connect(self.goToSavedPositions)
        self.ui.selectMachineFileButton.clicked.connect(self.selectMachine)
        self.ui.postProcFileBtn.clicked.connect(self.openPostProcFile)
        self.ui.postProcEditBtn.clicked.connect(self.editPostProcParam)
        self.ui.postProcClearLogBtn.clicked.connect(self.clearPostProcLog)
        self.ui.detailedSettingsButton.clicked.connect(self.detailedSettings)
        self.ui.presetButton.clicked.connect(self.presetModifiedPositions)

        # Sensor window detached
#        self.subWindow.topLevelChanged.connect(lambda toplevel: self.topLevelChanged(self.geometry, toplevel))
        self.subWindow.visibilityChanged.connect(lambda visible: self.visivilityChanged(self.geometry, visible))

        # set validator of line edit
        self.ui.IRonMultiplier.setValidator(QtGui.QDoubleValidator(0.0, 100.0, 2, self.ui.IRonMultiplier))
        self.ui.IRoffMultiplier.setValidator(QtGui.QDoubleValidator(0.0, 100.0, 2, self.ui.IRoffMultiplier))

        # line edit
        self.ui.IRonMultiplier.textChanged.connect(self.setMultiplier)
        self.ui.IRoffMultiplier.textChanged.connect(self.setMultiplier)
        self.ui.isoValue.currentTextChanged.connect(self.setMultiplier)

        # label
        self.ui.baseFolderName_label.setText(os.path.abspath(self.scriptParams.baseFolderName))
        self.ui.subFolderName_label.setText(self.scriptParams.subFolderName)

        # before Initialize
        self.restoreConfig()

        self.machineParams = {}
        self.previousMachineIni = 'data/previousMachine.ini'
        if os.path.exists(self.previousMachineIni):
            self.previousMachineFilePath = ini.getPreviousMachineFile(self.previousMachineIni)
            self.setMachine(self.previousMachineFilePath)


    def restoreConfig(self):
        if os.path.exists(self.configIniFile):
            # postproc file
            self.previousPostProcFilePath = ini.getPreviousPostProcFile(self.configIniFile)
            self.readPostProcFile()


    def resizeEvent(self, QResizeEvent):
        print("mainwindow resize event", self.size(), "ismaximized:", self.isMaximized())
        sender = self.sender()
        print(sender)
        if self.isMaximized() and (self.size().width() >= self.maxWinWidth
                                   or self.size().height() >= self.maxWinHeight):
            print("  isMaximized and size > maxsize")
            self.isMaxWinSize = True
            if self.subWindow.isHidden():
                print("show subwindow")
                self.showSubWindow(self.geometry, self.framesize)
            if self.subWindow.isFloating():
                print("setFloating false")
                self.subWindow.setFloating(False)
            self.subWindow.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)

            self.maxWinWidth = self.size().width()
            self.maxWinHeight = self.size().height()
        else:
            print("  not maximized")
            self.isMaxWinSize = False
            self.subWindow.setFeatures(QtWidgets.QDockWidget.DockWidgetClosable | QtWidgets.QDockWidget.DockWidgetFloatable)
            if self.isMaximized():
                print("  but ismMaximized")
                self.showNormal()
                self.setMinimumWidth(1040)
                self.setMaximumWidth(self.geometry.width())

    def get_key_from_value(self, d, val):  # https://note.nkmk.me/python-dict-get-key-from-value/
        keys = [k for k, v in d.items() if v == val]
        if keys:
            return keys[0]
        return None

    def closeEvent(self, event):  # https://www.qtcentre.org/threads/20895-PyQt4-Want-to-connect-a-window-s-close-button
        self.deleteLater()
        event.accept()
        self.subWindow.close()  # mainwindowが閉じたらsubwindowも閉じる
        exit()

    def make_motorGUI(self):
        # make dictionaries of member valuables
        exeButtons: dict = {}
        posSpinboxes: dict = {}
        speedSpinboxes: dict = {}
        currentPosLabels: dict = {}

        for m_name in self.motorSet:
            # https://teratail.com/questions/51674
            exeButtonsCode: str = '%s[\'%s\'] = %s%s%s' % (
                'exeButtons', m_name, 'self.ui.', m_name, 'MoveExe')  # exeButtons[~~] = self.ui.~~MoveExe
            exec(exeButtonsCode)
            posSpinCode = '%s[\'%s\'] = %s%s%s' % (
                'posSpinboxes', m_name, 'self.ui.', m_name, 'PosSpin')  # posSpinboxes[~~] = self.ui.~~PosSpin
            exec(posSpinCode)
            speedSpinCode = '%s[\'%s\'] = %s%s%s' % (
                'speedSpinboxes', m_name, 'self.ui.', m_name, 'SpeedSpin')  # speedSpinboxes[~~] = self.ui.~~SpeedSpin
            exec(speedSpinCode)
            speedSpinCode = '%s[\'%s\'] = %s%s%s' % (
                'currentPosLabels', m_name, 'self.ui.', m_name,
                'CurrentPos')  # currentPosLabels[~~] = self.ui.~~CurrentPos
            exec(speedSpinCode)

        # print(exeButtons)
        self.motorGUI['exe'] = exeButtons  # ex.) motorGUI['exe']['slider'] == self.ui.sliderMoveExe
        self.motorGUI['posSpin'] = posSpinboxes  # ex.) motorGUI['posSpin']['slider'] == self.ui.sliderPosSpin
        self.motorGUI['speedSpin'] = speedSpinboxes  # ex.) motorGUI['speedSpin']['slider'] == self.ui.sliderSpeedSpin
        self.motorGUI['currentPosLabel'] = currentPosLabels  # ex.) motorGUI['currentPosLabel']['slider'] == self.ui.sliderCurrentLabel

    def initializeMotors(self):
        count = 0

        # GUI
        print('Initialize Button was clicked')
        self.ui.initializeProgressBar.setEnabled(True)
        self.ui.initializeProgressLabel.setEnabled(True)
        self.ui.initializeProgressLabel.setText('Initializing...')
        count += 10
        self.ui.initializeProgressBar.setValue(count)

        # Motor
        if "motors" in self.machineParams:
            self.motorRobot = KeiganMotorRobot(self.machineParams["motors"])
        else:
            self.motorRobot = KeiganMotorRobot()

        self.motorRobot.getMotorDic()
        self.ui.initializeProgressBar.setValue(40)

        ### detailed settings window
        self.detailedSettingsWindow = DetailedSettingsWindow(mainUI=self)

        if self.motorRobot.initializeMotors():
            self.ui.initializeProgressBar.setValue(80)

            self.devices['motors'] = self.motorRobot.params
            self.devices['robot'] = self.motorRobot

            # IR light
            if "IRLight" in self.machineParams:
                IRtype = self.machineParams["IRLight"].get("type")
                IRdevice = self.machineParams["IRLight"].get("device")
                if IRtype == "MkE":
                    self.IRLight = IRLightMkE.IRLightMkE(IRtype, IRdevice)
                elif IRtype == "PAPOUCH":
                    self.IRLight = IRLightPapouch.IRLightPapouch(IRtype, IRdevice)
                elif IRtype == "Numato":
                    self.IRLight = IRLightNumato.IRLightNumato(IRtype, IRdevice)
                else:   # dummy
                    self.IRLight = IRLightDummy.IRLightDummy(IRtype, IRdevice)

            self.openIR()

            # GUI
            print('--initialization completed--')
            self.ui.initializeProgressBar.setValue(100)
            self.ui.initializeProgressLabel.setText('Initialized all motors')

            self.states = {UIState.MOTOR, UIState.IRLIGHT, UIState.SCRIPT}
            self.setUIStatus(self.states)
        else:
            QtWidgets.QMessageBox.critical(self, "Initialization Error",
                           "Couldn\'t initialize motors.\nPlease check if the motors are ready to be initialized.")
            self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}
            self.setUIStatus(self.states)

    def getCurrentPos(self):
        pos_d = self.motorRobot.getCurrentPos()
        self.updateCurrentPos(pos_d)
        self.judgePresetEnable()

    def updateCurrentPos(self, pos_d):
        for k, pos in pos_d.items():
            self.motorGUI['currentPosLabel'][k].setText('{:.2f}'.format(pos))

    def changeMovRoboStatus(self, pos_d, initial_err, err):
        self.updateCurrentPos(pos_d)
        if initial_err != 0:
            progress = (1-(err / initial_err))*100
            self.ui.initializeProgressBar.setValue(int(progress))

    def initSliderOrigin(self):
        m = self.motorRobot.slider
        m.speed(10.0)
        m.maxTorque(1.0)
        m.runForward()
        time.sleep(0.2)
        startTime = time.time()
        while True:
            (pos, vel, torque) = m.read_motor_measurement()
            if vel < 0.1:
                if time.time() - startTime > 2.0:
                    break
            else:
                startTime = time.time()

        m.presetPosition(0)
        m.free()
        QtWidgets.QMessageBox.information(self, "Slider origin", "Current position of slider is 0 mm.")
        m.maxTorque(5.0)
        self.moveRobot({'slider': 10.0})

    def freeAllMotors(self):
        for p in self.motorRobot.params.values():
            p['cont'].free()
        QtWidgets.QMessageBox.information(self, "free", "All motors have been freed.")

    def updateSpeed(self, speedSpinName):
        motorID = speedSpinName.replace('SpeedSpin', '')
        m = self.motorRobot.params[motorID]['cont']
        m.speed(self.motorGUI['speedSpin'][motorID].value())

    def exeButtonClicked(self, buttonName):
        if re.search('.+MoveExe', buttonName):
            self.judgePresetEnable()
            motor_id = buttonName.replace('MoveExe', '')
            targetPos = self.motorGUI['posSpin'][motor_id].value()
            targetPos_d = {motor_id: targetPos}
            self.moveRobot(targetPos_d)

    def judgePresetEnable(self):
        modified = False
        for v in self.motorGUI['posSpin'].values():
            if type(v) is MyDoubleSpinBox.MyDoubleSpinBox:
                if v.isModified():
                    modified = True
                    break
        self.ui.presetButton.setEnabled(modified)

    def presetModifiedPositions(self):
        for k, v in self.motorGUI['posSpin'].items():
            if type(v) is MyDoubleSpinBox.MyDoubleSpinBox:
                if v.isModified():
                    pos_d = {k: v.value()}
                    self.presetPositions(pos_d)
        self.judgePresetEnable()

    def presetPositions(self, pos_d):
        self.updateTargetPosition(pos_d)
        self.updateCurrentPos(pos_d)
        self.motorRobot.presetPos(pos_d)

    def rebootButtonClicked(self):
        self.motorRobot.reboot()
        self.states = {UIState.MACHINEFILE, UIState.INITIALIZE, UIState.IRLIGHT}
        self.setUIStatus(self.states)
        QtWidgets.QMessageBox.information(self, "reboot", "All motors have been rebooted. \n"
                                                          "Please re-initialize motors to use again.")

    def moveRobot(self, targetpos):
        self.updateActionProgress(0, 'Moving...', True)

        isAborted = self.motorRobot.goToTargetPos(targetpos, self.changeMovRoboStatus)
        if isAborted:
            QtWidgets.QMessageBox.critical(self, "Timeout Error", "Motor not moving.")
        else:
            self.updateActionProgress(100, 'Goal', False)
            self.updateTargetPosition(targetpos)
            if self.subWindow.connected:
                self.subWindow.prevImg(1)
        time.sleep(0.1)
        self.getCurrentPos()

    def updateTargetPosition(self, targetpos):
        for k in targetpos.keys():
            posspin = self.motorGUI['posSpin'].get(k)
            if type(posspin) is MyDoubleSpinBox.MyDoubleSpinBox:
                posspin.setValue(targetpos[k])
        self.judgePresetEnable()

    def updateActionProgress(self, value, text, active):
        self.ui.initializeProgressBar.setValue(value)
        self.ui.initializeProgressLabel.setText(text)
        self.ui.initializeProgressBar.setEnabled(active)
        self.ui.initializeProgressLabel.setEnabled(active)

    # --- Scripting

    def openScriptFile(self):
        previousScriptPath = ''
        previousScriptDir = './script/'
        previousScript_iniFile = 'data/previousScript.ini'
        if os.path.exists('data/previousScript.ini'):
            previousScriptPath = ini.getPreviousScriptPath(previousScript_iniFile)
            if os.path.exists(previousScriptPath):
                previousScriptDir = os.path.dirname(previousScriptPath)

        (fileName, selectedFilter) = \
            QtWidgets.QFileDialog.getOpenFileName(self, 'Select script', previousScriptDir, '*.txt')

        if fileName == '':  # when cancel pressed
            if self.scriptParams.scriptName == '':
                self.ui.scriptName_label.setText('')
                self.scriptParams.scriptName = fileName
                self.scriptParams.commandNum = 0
            else:
                pass
        else:
            ini.updatePreviousScriptPath(previousScript_iniFile, fileName)

            self.ui.scriptName_label.setText(
                os.path.basename(fileName))

            self.scriptParams.scriptName = fileName
            self.scriptParams.commandNum = execute_script.countCommandNum(self.scriptParams, [], [])
            self.total = self.scriptParams.commandNum
            self.done = 0
            self.updateScriptProgress()


    def openBaseFolder(self):
        fileName = \
            QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder')

        if fileName == '':  # when cancel pressed
            pass
        else:
            self.ui.baseFolderName_label.setText(os.path.abspath(fileName))
            self.scriptParams.baseFolderName = fileName

    def openSubFolder(self):
        fileName = \
            QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder', self.scriptParams.baseFolderName + '/')

        if fileName == '':  # when cancel pressed
            pass
        else:
            self.ui.subFolderName_label.setText(os.path.basename(fileName))
            self.scriptParams.subFolderName = os.path.basename(fileName)

    def dataOutFolder(self):
        return self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName

    def renewSubFolder(self):
        self.scriptParams.renewSubFolderName()
        self.ui.subFolderName_label.setText(self.scriptParams.subFolderName)

    def demo(self, isContinue):
        self.scriptParams.scriptName = self.demo_script
        self.ui.scriptName_label.setText(self.demo_script)
        self.scriptParams.isContinue = isContinue

        if isContinue:
            self.scriptParams.start_command_num = self.done
        else:
            self.scriptParams.start_command_num = 0

        if not os.path.exists(self.demo_script):
            QtWidgets.QMessageBox.critical \
                (self, "File",
                 'Demo script doesn\'t exist. \n '
                 'Please check \" ~'
                 + os.path.abspath(os.getcwd()) + self.demo_script.replace("./", "/") + '\"')
            # https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory

        else:
            self.states = {UIState.SCRIPT_PROGRESS}
            self.setUIStatus(self.states)

            interrupted = execute_script.execute_script(self.scriptParams, self.devices, self, True)

            self.states = {UIState.SCRIPT, UIState.MOTOR, UIState.IRLIGHT}
            self.setUIStatus(self.states)

            if not interrupted:
                QtWidgets.QMessageBox.information(self, "Finish scripting!", "All commands in \n"
                                                                         "the demo file \nhave been completed.")

        self.scriptParams.scriptName = self.ui.scriptName_label.text()

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.interrupt()

    def run_script(self, isContinue):
        self.stopClicked = False

        if self.scriptParams.scriptName == self.demo_script:
            self.demo(isContinue)
            return

        if isContinue:
            self.scriptParams.isContinue = True
            if self.scriptParams.subFolderName == '':
                self.openSubFolder()
            if os.path.exists(self.scriptParams.baseFolderName + '/'
                              + self.scriptParams.subFolderName + '/'
                              + 'Log.ini'):

                previouslyExecutedScriptName = os.path.basename(ini.loadIni(
                    self.dataOutFolder()))
                # previouslyExecutedScriptDir = os.path.dirname(ini.loadIni(
                #     self.dataOutFolder()))
                previouslyExecutedScript = ini.loadIni(
                    self.dataOutFolder())

                qm = MyMessageBox()

                if self.ui.scriptName_label.text() != previouslyExecutedScriptName:
                    # ret = QtWidgets.QMessageBox.question \
                    ret = qm.question \
                                (self, 'Which script to execute?', "The previously executed script is different from what you selected.\n"
                                   "- The previous one: \"" + previouslyExecutedScriptName +"\"\n"
                                    "- The one you selected: \"" + self.ui.scriptName_label.text() + "\"\n"
                                    "Click [Yes] to continue the former, or [No] to execute the latter from the top.",
                         qm.Yes | qm.No)

                    if ret == qm.Yes:
                        self.scriptParams.scriptName = previouslyExecutedScript
                    elif ret == qm.No:
                        # self.scriptParams.scriptName = self.ui.scriptName_label.text()
                        pass
                    else:
                        return
                self.ui.scriptName_label.setText(os.path.basename(self.scriptParams.scriptName))
        else:
            self.scriptParams.isContinue = False
            self.renewSubFolder()

        if self.scriptParams.scriptName == '' or not self.scriptParams:
            self.openScriptFile()
        if self.scriptParams.scriptName == '' or not self.scriptParams:
            return

        if not os.path.exists(self.dataOutFolder()):
            os.makedirs(self.dataOutFolder())

        self.showSubWindow(self.geometry, self.framesize)

        # GUI
        if self.devices['3Dsensors'].connected:
            self.devices['3Dsensors'].sensorInfo.save_to_file(self.dataOutFolder() + "/sensorinfo.json")

        self.states = {UIState.SCRIPT_PROGRESS}
        self.setUIStatus(self.states)

        ### EXECUTE
        interrupted = execute_script.execute_script(self.scriptParams, self.devices, self)

        self.states = {UIState.SCRIPT, UIState.MOTOR, UIState.IRLIGHT}
        self.setUIStatus(self.states)

        if not interrupted:
            # mixer.music.play(1)
            playsound("SE/finish_chime.mp3")    # https://qiita.com/hisshi00/items/62c555095b8ff15f9dd2
            if self.ui.PostProc_groupBox.isChecked():
                self.doPostProc()
            QtWidgets.QMessageBox.information(self, "Finish scripting!", "All commands in \n"
                                                                         "\"%s\" \nhave been completed."
                                              % os.path.basename(self.scriptParams.scriptName))


    def setHome(self):
        targetPos_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        self.presetPositions(targetPos_d)

    def goToHomePosition(self):
        targetPos_d = {'slider': 0.0, 'pan': 0.0, 'tilt': 0.0}
        self.updateTargetPosition(targetPos_d)
        self.moveRobot(targetPos_d)

    def savePositions(self):
        save_name = ''
        for posspin in self.motorGUI['posSpin'].values():
            save_name += str('{:.2f}'.format(posspin.value())) + ' '
            save_name.strip()  # https://itsakura.com/python-strip#s2
        if not save_name in [self.ui.savedPosCombo.itemText(i) for i in range(
                self.ui.savedPosCombo.count())]:  # https://stackoverflow.com/questions/7479915/getting-all-items-of-qcombobox-pyqt4-python
            self.ui.savedPosCombo.addItem(save_name)
        print(save_name)

    def goToSavedPositions(self):
        targetPos = self.ui.savedPosCombo.currentText().split()  # list
        targetPos_d = {'slider': float(targetPos[0]), 'pan': float(targetPos[1]), 'tilt': float(targetPos[2])}
        self.updateTargetPosition(targetPos_d)
        self.moveRobot(targetPos_d)

    def showSubWindow(self, geometry, framesize):
        if self.subWindow_isOpen:
            self.subWindow.activateWindow()
            self.subWindow.show()
        else:
            self.subWindow.show()
            self.subWindow.move(geometry.width() / 2 - framesize.width() / 16,
                                geometry.height() / 2 - framesize.height() / 3)
            self.subWindow_isOpen = True
        self.restoreDockWidget(self.subWindow)
        # self.subWindow.resize(QtCore.QSize(909, 616))   # windowがfloatingしてるときはworkする。。

    def openIR(self):
        message = self.IRLight.open()
        self.devices['lights'] = self.IRLight

        self.ui.IRstateLabel.setText(message)

    def IRlightControl(self, ch, state):
        self.IRLight.set(ch, state)

    def toFloat(self, text, default):
        try:
            val = float(text)
            return val
        except ValueError:
            return default

    def setMultiplier(self):
        self.scriptParams.IRonMultiplier = self.toFloat(self.ui.IRonMultiplier.text(), 1.0)
        self.scriptParams.IRoffMultiplier = self.toFloat(self.ui.IRoffMultiplier.text(), 1.0)
        self.scriptParams.isoValue = self.ui.isoValue.currentText()


    def topLevelChanged(self, geometry, toplevel):
        print("toplevelChanged", toplevel)
        self.changeMainWinSize(geometry)

    def visivilityChanged(self, geometry, visible):
        print("visivilityChanged", visible)
        self.changeMainWinSize(geometry)

    def changeMainWinSize(self, geometry):
        posX = self.pos().x()
        posY = self.pos().y()
        mainWidth = self.frameGeometry().width()
        mainHeight = self.frameGeometry().height()
        print('changeMainWinSize')

        if not self.isMaxWinSize:
            if self.subWindow.isFloating() or self.subWindow.isHidden():
                print("isFloating:", self.subWindow.isFloating(), " isHidden:", self.subWindow.isHidden())
                self.showNormal()
                self.setMinimumWidth(540)
                self.setMaximumWidth(self.minimumWidth())
                self.setGeometry(posX, posY, self.minimumWidth(), self.size().height())
            else:
                print("  docked")
                self.showNormal()
                self.setMinimumWidth(self.minimumWidth()+self.subWindow.minimumWidth())
                self.setMinimumWidth(1040)
                self.setMaximumWidth(geometry.width())
                self.setGeometry(posX, posY, self.minimumWidth(), max(mainHeight, self.sensorWinHeight))
                ### for check ###
                # print('isFloating: ' + str(self.subWindow.isFloating()))
                # print('isHidden: ' + str(self.subWindow.isHidden()))
                # print('isMaximized: ' + str(self.isMaximized()))
                # print('isMaxWinSize: ' + str(self.isMaxWinSize))
                # print('minimumWidth: ' + str(self.minimumWidth()))
                # print('-----')

    # ----- detailed settings -----
    def detailedSettings(self):
        self.detailedSettingsWindow.pidChanged.connect(self.motorRobot.changePIDparam)

        self.detailedSettingsWindow.activateWindow()
        self.detailedSettingsWindow.move(self.pos().x()+500, self.pos().y())
        self.detailedSettingsWindow.show()

    # ----- Post Process -----

    def readPostProcFile(self):
        if os.path.exists(self.previousPostProcFilePath):
            self.ui.postProcFilelabel.setText(os.path.basename(self.previousPostProcFilePath))
            with open(self.previousPostProcFilePath) as f:
                self.postproc = json.load(f)

    def openPostProcFile(self):
        (fileName, selectedFilter) = \
            QtWidgets.QFileDialog.getOpenFileName(self, 'Select Post Process File', 'postproc', '*.json')

        if fileName == '':  # when cancel pressed
            pass
        else:
            self.previousPostProcFilePath = fileName
            ini.updatePreviousPostProcFile(self.configIniFile, self.previousPostProcFilePath)
            self.readPostProcFile()

    def editPostProcParam(self):
        subprocess.Popen(['xdg-open ' + self.previousPostProcFilePath], shell=True)

    def clearPostProcLog(self):
        self.ui.postProcLogTextEdit.clear()

    def doPostProc(self):
        info = SensorInfo()
        info.clear()
        info.load_from_file(self.dataOutFolder() + "/sensorinfo.json")
        self.ui.postProcLogTextEdit.append("exec postproc: " + info.labelid + "_" + self.scriptParams.subFolderName)
        self.ui.postProcLogTextEdit.ensureCursorVisible()

        proc = subprocess.Popen(
            'gnome-terminal --  bash -c "' +
            self.postproc['program'] + ' ' + self.dataOutFolder() + ' ' + self.previousPostProcFilePath + ' ;exec bash"', shell=True)

        # with subprocess.Popen(self.postproc['program'] + ' ' + self.dataOutFolder() + ' ' + self.previousPostProcFilePath,
        #                       shell=True, encoding='UTF-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        # while True:
        #         # バッファから1行読み込む.
        #         line = proc.stdout.readline()
        #         self.ui.postProcLogTextEdit.append(line)
        #         proc.stdout.flush()
        #         app.processEvents()
        #
        #
        #         # バッファが空 + プロセス終了.
        #         if not line and proc.poll() is not None:
        #             break

    # ----- UI-related functions -----
    def setUIStatus(self, status):
        if UIState.MACHINEFILE in status:
            self.ui.selectMachineFileButton.setEnabled(True)
        else:
            self.ui.selectMachineFileButton.setEnabled(False)

        if UIState.INITIALIZE in status:
            self.ui.initializeButton.setEnabled(True)
            self.ui.initializeProgressBar.setEnabled(True)
            self.ui.initializeProgressBar.setValue(0)
            self.ui.initializeProgressLabel.setEnabled(True)
            self.ui.initializeProgressLabel.setText('Push \"Initialize\"')
        else:
            self.ui.initializeButton.setEnabled(False)
            self.ui.initializeProgressBar.setEnabled(False)
            self.ui.initializeProgressLabel.setEnabled(False)
            # self.ui.initializeProgressLabel.setText('Initialized all motors')

        if UIState.MOTOR in status:
            # self.ui.robotControl.setEnabled(True)
            self.ui.manualOperation.setEnabled(True)
            self.ui.MagikEye.setEnabled(True)
            self.ui.getCurrentPosButton.setEnabled(True)
            self.ui.detailedSettingsButton.setEnabled(True)
        else:
            self.ui.manualOperation.setEnabled(False)
            self.ui.MagikEye.setEnabled(False)
            self.ui.getCurrentPosButton.setEnabled(False)
            self.ui.detailedSettingsButton.setEnabled(False)

        if UIState.IRLIGHT in status and self.IRLight.isvalid():
            self.ui.SectionIRlightControl.setEnabled(True)
        else:
            self.ui.SectionIRlightControl.setEnabled(False)

        if UIState.SCRIPT in status:
            self.ui.selectScript_toolButton.setEnabled(True)
            self.ui.selectBaseFolder_toolButton.setEnabled(True)
            self.ui.selectSubFolder_toolButton.setEnabled(True)
            self.ui.renewSubFolder_toolButton.setEnabled(True)
            self.ui.continueButton.setEnabled(True)
            self.ui.executeScript_button.setEnabled(True)
            self.subWindow.ui_s.SectionCameraControl.setEnabled(True)
            self.subWindow.ui_s.SectionLaserControl.setEnabled(True)
        else:
            self.ui.selectScript_toolButton.setEnabled(False)
            self.ui.selectBaseFolder_toolButton.setEnabled(False)
            self.ui.selectSubFolder_toolButton.setEnabled(False)
            self.ui.renewSubFolder_toolButton.setEnabled(False)
            self.ui.continueButton.setEnabled(False)
            self.ui.executeScript_button.setEnabled(False)
            self.subWindow.ui_s.SectionCameraControl.setEnabled(False)
            self.subWindow.ui_s.SectionLaserControl.setEnabled(False)

        if UIState.SCRIPT_PROGRESS in status:
            self.ui.progressBar.setEnabled(True)
            self.ui.stopButton.setEnabled(True)
        else:
            self.ui.progressBar.setEnabled(False)
            self.ui.stopButton.setEnabled(False)


# ----- Scripting-related functions -----
    def updatePercentage(self):
        if self.total > 0:
            self.percent = self.done / self.total * 100
        else:
            self.percent = 0.0
        # print(self.percent)
        self.ui.progressBar.setValue(self.percent)
        return self.percent

    def updateProgressLabel(self):
        self.ui.progressLabel.setText(str(self.done) + ' / ' + str(self.total))

    def updateScriptProgress(self):
        self.updateProgressLabel()
        self.updatePercentage()

    def interrupt(self):
        self.stopClicked = True
# ==================================================================

# ----- Select machine -----
    def selectMachine(self):
        (fileName, selectedFilter) = \
            QtWidgets.QFileDialog.getOpenFileName(self, 'Select script', 'machineFiles', '*.json')

        if fileName == '':  # when cancel pressed
            pass
        else:
            self.setMachine(fileName)


    def setMachine(self, filename):
        if os.path.exists(filename):
            self.machineParams = json_IO.loadJson(filename)
            self.previousMachineFilePath = filename
            ini.updatePreviousMachineFile('data/previousMachine.ini', filename)
            self.ui.machineFileName_label.setText(os.path.basename(filename))

        if self.machineParams == {}:
            self.states = {UIState.MACHINEFILE}
        else:
            self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}

        self.setUIStatus(self.states)


    # ==================================================================
    def sensorChanged(self, connected):
        print('changed')
        # if connected:
        # else:

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(':/MkECTL.png'))
    keiganWindow = Ui()
    keiganWindow.show()
    # sensorWindow = SensorWindow()
    app.exec_()

