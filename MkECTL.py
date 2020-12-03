#!/usr/bin/env python3
# coding: utf-8

from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys
import time
import os
import re
import serial
from functools import partial
import datetime
import math

import MyDoubleSpinBox
import motordic
import mainwindow_ui
import execute_script
import sensors
import ini
import read_machine_file
from UIState import UIState

import IRLightMkE
import IRLightPapouch
import IRLightDummy
from IMainUI import IMainUI

class ScriptParams():
    def __init__(self):
        self.now = datetime.datetime.now()

        self.execTwoScr: bool = False
        self.scriptName: str = ''
        self.scriptName_2: str = ''
        self.commandNum_1: int = 0
        self.commandNum_2: int = 0
        self.commandNum_total: int = 0
        self.baseFolderName: str = 'data'
        self.subFolderName: str = self.now.strftime('%Y%m%d_%H%M%S')
        self.isContinue = False

        self.IRonMultiplier = 1.0
        self.IRoffMultiplier = 1.0

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

class Ui(QtWidgets.QMainWindow, IMainUI):
    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.ui = mainwindow_ui.Ui_mainwindow()
        self.ui.setupUi(self)
        self.scriptParams = ScriptParams()

        self.subWindow = sensors.SensorWindow(mainUI=self)

        self.initializeProcessFlag = False

        self.ui.manualOperation.setEnabled(False)
        self.ui.IRlightControlGroup.setEnabled(False)
        self.ui.continueButton.setEnabled(False)
        self.ui.executeScript_button.setEnabled(False)
        self.ui.Scripting_groupBox.setEnabled(False)

        # IR light
        self.isPortOpen = True
        self.IRport = None
        self.IRLight = None
        # self.openIR('/dev/ttyACM0')

        # scripting
        self.done = 0
        self.total = 100
        self.percent = 0
        self.stopClicked = False

        self.ui.progressLabel.setText(str(self.done) + ' / ' + str(self.total))
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
        self.move(self.geometry.width() / 2 - self.framesize.width(),
                  self.geometry.height() / 2 - self.framesize.height() / 2)

        # variables
        self.params = {}  # motorDic

        self.motorSet = ['slider', 'pan', 'tilt']
        self.devices: dict = {}  # 'motors', 'lights', '3Dsensors' etc.  # Dict of dictionaries
        self.motors: dict = {}  # 'slider', 'pan', 'tilt' (may not have to be a member val)
        self.motorGUI: dict = {}  # 'exe', 'posSpin', 'speedSpin', 'currentPosLabel'  # GUI objects related to motors  # Dict of dictionaries
        self.subWindow_isOpen = False
        self.states = set()

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
            self.motorGUI['exe'][m_name].clicked.connect(partial(lambda n: self.exeButtonClicked(n), exeButtonName))
            # position spinboxes
            self.motorGUI['posSpin'][m_name].setKeyboardTracking(False)
            self.motorGUI['posSpin'][m_name].valueChanged.connect(partial(lambda n: self.exeButtonClicked(n), exeButtonName))
            self.motorGUI['posSpin'][m_name].returnPressed.connect(partial(lambda n: self.exeButtonClicked(n), exeButtonName))
            # speed spinboxes
            self.motorGUI['speedSpin'][m_name].setKeyboardTracking(False)
            self.motorGUI['speedSpin'][m_name].valueChanged.connect(partial(lambda n: self.updateSpeed(n), speedSpinName))
            # https://melpon.hatenadiary.org/entry/20121206/1354636589

        self.ui.presetExe.clicked.connect(lambda: self.exeButtonClicked('presetExe'))
        self.ui.rebootButton.clicked.connect(self.rebootButtonClicked)

        # other buttons
        self.ui.initializeButton.setEnabled(False)
        self.ui.initializeButton.clicked.connect(self.initializeMotors)
        self.ui.MagikEye.clicked.connect(self.demo)
        self.ui.selectScript_toolButton.clicked.connect(lambda: self.openScriptFile(1))
        self.ui.selectScript_toolButton_2.clicked.connect(lambda: self.openScriptFile(2))
        self.ui.delete2ndScriptButton.clicked.connect(lambda: self.delete2ndScript)
        self.ui.selectBaseFolder_toolButton.clicked.connect(self.openBaseFolder)
        self.ui.selectSubFolder_toolButton.clicked.connect(self.openSubFolder)
        self.ui.renewSubFolder_toolButton.clicked.connect(self.renewSubFolder)
        self.ui.executeScript_button.clicked.connect(lambda: self.run_2scripts(False))
        self.ui.continueButton.clicked.connect(lambda: self.run_2scripts(True))
        self.ui.delete2ndScriptButton.clicked.connect(self.delete2ndScript)
        self.ui.viewSensorWinButton.clicked.connect(lambda: self.showSubWindow(self.geometry, self.framesize))
        self.ui.sliderOriginButton.clicked.connect(self.setSliderOrigin)
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

        # Combo box event
        self.ui.presetMotorCombo.currentTextChanged.connect(self.changeUnitLabel)

        # set validator of line edit
        self.ui.presetValue.setValidator(QtGui.QDoubleValidator(-100.0, 2100.0, 2, self.ui.presetValue))
        self.ui.IRonMultiplier.setValidator(QtGui.QDoubleValidator(0.0, 100.0, 2, self.ui.IRonMultiplier))
        self.ui.IRoffMultiplier.setValidator(QtGui.QDoubleValidator(0.0, 100.0, 2, self.ui.IRoffMultiplier))

        # line edit
        self.ui.IRonMultiplier.textChanged.connect(self.setMultiplier)
        self.ui.IRoffMultiplier.textChanged.connect(self.setMultiplier)

        # label
        self.ui.baseFolderName_label.setText(os.path.abspath(self.scriptParams.baseFolderName))
        self.ui.subFolderName_label.setText(self.scriptParams.subFolderName)

        # before Initialize
        self.machineParams = {}
        self.previousMachineIni = 'data/previousMachine.ini'
        self.previousMachineFilePath = ''
        if os.path.exists(self.previousMachineIni):
            self.previousMachineFilePath = ini.getPreviousMachineFile(self.previousMachineIni)
            if os.path.exists(self.previousMachineFilePath):
                self.machineParams = read_machine_file.loadJson(self.previousMachineFilePath)
                self.ui.initializeButton.setEnabled(True)
            self.ui.machineFileName_label.setText(os.path.basename(self.previousMachineFilePath))

        if self.machineParams == {}:
            self.states = {UIState.MACHINEFILE}
            self.setUIStatus(self.states)
        else:
            self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}
            self.setUIStatus(self.states)

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
        self.motorGUI[
            'currentPosLabel'] = currentPosLabels  # ex.) motorGUI['currentPosLabel']['slider'] == self.ui.sliderCurrentLabel

    def initializeMotors(self):
        count = 0

        print('Initialize Button was clicked')
        self.ui.initializeProgressBar.setEnabled(True)
        self.ui.initializeProgressLabel.setEnabled(True)
        self.ui.initializeProgressLabel.setText('Initializing...')
        count += 10
        self.ui.initializeProgressBar.setValue(count)

        if "motors" in self.machineParams:
            self.params = motordic.getMotorDic(self.machineParams["motors"])
        else:
            self.params = motordic.getMotorDic()

        for p in self.params.values():  # https://note.nkmk.me/python-dict-in-values-items/

            m = p['cont']
            m.enable()
            m.interface(8)  # USB

            m.speed(self.motorGUI['speedSpin'][p['id']].value())
            print(p['id'] + 'speed  = ' + str(self.motorGUI['speedSpin'][p['id']].value()) + 'rad/s')

            self.motors[p['id']] = m  # member valuable of class

            count += 30
            time.sleep(0.2)
            self.ui.initializeProgressBar.setValue(count)

        self.devices['motors'] = self.motors

        # set motor initial parametors
        m = self.motors['slider']
        m.enable()
        m.curveType(1)
        m.maxSpeed(250)
        m.acc(8)
        m.dec(8)
        m.speed(20)
        m.maxTorque(5)

        m = self.motors['pan']
        m.enable()
        m.curveType(1)
        m.maxSpeed(250)
        m.acc(2)
        m.dec(2)
        m.speed(7)
        m.maxTorque(5)

        m = self.motors['tilt']
        m.enable()
        m.curveType(1)
        m.maxSpeed(250)
        m.acc(2)
        m.dec(2)
        m.speed(7)
        m.maxTorque(5)

        # IR light
        if "IRLight" in self.machineParams:
            IRtype = self.machineParams["IRLight"].get("type")
            IRdevice = self.machineParams["IRLight"].get("device")
            if IRtype == "MkE":
                self.IRLight = IRLightMkE.IRLightMkE(IRtype, IRdevice)
            elif IRtype == "PAPOUCH":
                self.IRLight = IRLightPapouch.IRLightPapouch(IRtype, IRdevice)
            else:   # dummy
                self.IRLight = IRLightDummy.IRLightDummy(IRtype, IRdevice)

        self.openIR()

        # GUI
        print('--initialization completed--')
        self.ui.initializeProgressBar.setValue(100)
        # self.ui.initializeButton.setEnabled(False)
        # self.ui.initializeProgressBar.setEnabled(False)
        self.ui.initializeProgressLabel.setText('Initialized all motors')
        # self.ui.manualOperation.setEnabled(True)
        # self.ui.IRlightControlGroup.setEnabled(True)
        # self.ui.continueButton.setEnabled(True)
        # self.ui.executeScript_button.setEnabled(True)

        self.states = {UIState.MOTOR, UIState.IRLIGHT, UIState.SCRIPT}
        self.setUIStatus(self.states)

    def setSliderOrigin(self):
        m = self.motors['slider']
        # m = self.params['slider']['cont']
        # scale = self.params['slider']['scale']
        m.speed(10.0)
        m.maxTorque(1.0)
        m.runForward()
        time.sleep(0.2)
        startTime = time.time()
        while True:
            (pos, vel, torque) = m.read_motor_measurement()
            # print(torque)
            # print(vel)
            if vel < 0.1:
                if time.time() - startTime > 2.0:
                    break
            else:
                startTime = time.time()

        m.free()
        m.presetPosition(0)
        m.maxTorque(5.0)
        print('preset current position as 0 mm')
        print('-- slider origin has been set --')
        QtWidgets.QMessageBox.information(self, "Slider origin", "Current position of slider is 0 mm.")

    def freeAllMotors(self):
        for m in self.motors.values():
            m.free()
        QtWidgets.QMessageBox.information(self, "free", "All motors have been freed.")

        # print('--free completed--')

    def updateSpeed(self, speedSpinName):
        # print(speedSpinName)
        motorID = speedSpinName.replace('SpeedSpin', '')
        m = self.motors[motorID]
        m.speed(self.motorGUI['speedSpin'][motorID].value())

    def exeButtonClicked(self, buttonName):
        # print(buttonName)  # type->str
        if re.search('.+MoveExe', buttonName):
            motorID = buttonName.replace('MoveExe', '')
            m = self.motors[motorID]
            scale = self.params[motorID]['scale']
            motorPos = self.motorGUI['posSpin'][motorID].value()
            # m.speed(self.motorGUI['speedSpin'][motorID].value())
            m.moveTo(motorPos * scale)
            while True:
                error = 0.0
                time.sleep(0.2)

                (pos, vel, torque) = m.read_motor_measurement()
                error += pos - (motorPos * scale)

                if error < 0.1:
                    break

            self.motorGUI['currentPosLabel'][motorID].setText('{:.2f}'.format(motorPos))
            if self.subWindow.conn:
                self.subWindow.getImg(1)

        elif buttonName == 'presetExe':
            motorID = self.ui.presetMotorCombo.currentText()
            m = self.motors[motorID]
            # m = self.params[motorID]['cont']

            scale = self.params[motorID]['scale']
            pos = float(self.ui.presetValue.text())
            m.presetPosition(pos * scale)

            self.motorGUI['posSpin'][motorID].setValue(pos)

            self.motorGUI['currentPosLabel'][motorID].setText('{:.2f}'.format(pos))

    def rebootButtonClicked(self):
        for m in self.motors.values():
            m.reboot()
            m.close()

        # GUI
        # self.ui.initializeButton.setEnabled(True)
        # self.ui.initializeProgressBar.setValue(0)
        # self.ui.initializeProgressLabel.setText('Initializing motors...')
        # self.ui.manualOperation.setEnabled(False)
        # self.ui.IRlightControlGroup.setEnabled(False)
        # self.ui.continueButton.setEnabled(False)
        # self.ui.executeScript_button.setEnabled(False)

        self.states = {UIState.MACHINEFILE, UIState.INITIALIZE, UIState.IRLIGHT}
        self.setUIStatus(self.states)
        QtWidgets.QMessageBox.information(self, "reboot", "All motors have been rebooted. \n"
                                                          "Please re-initialize motors to use again.")

    def changeUnitLabel(self):
        motorID = self.ui.presetMotorCombo.currentText()
        if motorID == 'slider':
            self.ui.unitLabel.setText('mm')
        elif motorID == 'pan' or 'tilt':
            self.ui.unitLabel.setText('deg')

    def openScriptFile(self, num):  # https://www.xsim.info/articles/PySide/special-dialogs.html#OpenFile
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
            pass
        else:
            ini.updatePreviousScriptPath(previousScript_iniFile, fileName)

            if num == 1:
                self.ui.scriptName_label.setText(
                    os.path.basename(fileName))  # https://qiita.com/inon3135/items/f8ebe85ad0307e8ddd12
                self.scriptParams.scriptName = fileName
                self.scriptParams.commandNum_1 = execute_script.countCommandNum(self.scriptParams, [], [])
            else:
                self.ui.scriptName_label_2.setText(os.path.basename(fileName))
                self.scriptParams.scriptName_2 = fileName
                self.scriptParams.commandNum_2 = execute_script.countCommandNum(self.scriptParams, [], [])
                self.scriptParams.execTwoScr = True

            self.scriptParams.commandNum_total = self.scriptParams.commandNum_1 + self.scriptParams.commandNum_2
            self.ui.numOfCommands_label.setText(str(self.scriptParams.commandNum_total))

    def delete2ndScript(self):
        self.scriptParams.scriptName_2 = ''
        self.scriptParams.commandNum_2 = 0
        self.ui.scriptName_label_2.setText('')
        self.scriptParams.execTwoScr = False

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

    def renewSubFolder(self):
        self.scriptParams.renewSubFolderName()
        self.ui.subFolderName_label.setText(self.scriptParams.subFolderName)

    def demo(self):
        demo_script = 'script/demo.txt'
        self.scriptParams.scriptName = demo_script
        self.ui.scriptName_label.setText(demo_script)

        if not os.path.exists(demo_script):
            QtWidgets.QMessageBox.critical \
                (self, "File",
                 'Demo script doesn\'t exist. \n '
                 'Please check \" ~'
                 + os.path.abspath(os.getcwd()) + demo_script.replace("./", "/") + '\"')
            # https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory

        else:
            self.states = {UIState.SENSOR_CONNECTED, UIState.SCRIPT_PROGRESS}
            self.setUIStatus(self.states)
            # self.GUIwhenScripting(False)

            stopped = execute_script.execute_script(self.scriptParams, self.devices, self.params, self, True)

            self.states = {UIState.SCRIPT, UIState.MOTOR, UIState.IRLIGHT, UIState.SENSOR_CONNECTED}
            self.setUIStatus(self.states)
            # self.GUIwhenScripting(True)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.interrupt()

    def run_script(self, isContinue):
        self.stopClicked = False

        if isContinue:
            self.scriptParams.isContinue = True
            if self.scriptParams.subFolderName == '':
                self.openSubFolder()
            if os.path.exists(self.scriptParams.baseFolderName + '/'
                              + self.scriptParams.subFolderName + '/'
                              + 'Log.ini'):

                previouslyExecutedScriptName = os.path.basename(ini.loadIni(
                    self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName))
                # previouslyExecutedScriptDir = os.path.dirname(ini.loadIni(
                #     self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName))
                previouslyExecutedScript = ini.loadIni(
                    self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName)

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

        if self.scriptParams.scriptName == '':
            self.openScriptFile(1)

        if not os.path.exists(self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName):
            os.makedirs(self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName)

        self.showSubWindow(self.geometry, self.framesize)

        # GUI
        # self.GUIwhenScripting(False)
        self.states = {UIState.SENSOR_CONNECTED, UIState.SCRIPT_PROGRESS}
        self.setUIStatus(self.states)

        stopped = execute_script.execute_script(self.scriptParams, self.devices, self.params, self)

        # self.GUIwhenScripting(stopped)
        self.states = {UIState.SCRIPT, UIState.MOTOR, UIState.IRLIGHT, UIState.SENSOR_CONNECTED}
        self.setUIStatus(self.states)

    def run_2scripts(self, isContinue):
        if self.scriptParams.execTwoScr:
            self.run_script(isContinue)    # exec 1st script

            # -------- 2nd script -------
            # self.renewSubFolder()

            self.scriptParams.isContinue = False

            if self.scriptParams.scriptName_2 == '':
                self.openScriptFile(2)

            if not os.path.exists(self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName):
                os.makedirs(self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName)

            # self.showSubWindow(self.geometry, self.framesize)

            # GUI
            # self.GUIwhenScripting(False)
            self.states = {UIState.SENSOR_CONNECTED, UIState.SCRIPT_PROGRESS}
            self.setUIStatus(self.states)

            stopped = execute_script.execute_script(self.scriptParams, self.devices, self.params, self)

            # self.GUIwhenScripting(stopped)
            self.states = {UIState.SCRIPT, UIState.MOTOR, UIState.IRLIGHT, UIState.SENSOR_CONNECTED}
            self.setUIStatus(self.states)

            pass  # will be updated later

        else:
            self.run_script(isContinue)

    def setHome(self):
        for m in self.devices['motors'].values():
            m.presetPosition(0.0)
            self.motorGUI['posSpin'][self.get_key_from_value(self.devices['motors'], m)].setValue(0.0)

            self.motorGUI['currentPosLabel'][self.get_key_from_value(self.devices['motors'], m)].setText(
                '{:.2f}'.format(0.0))

    def goToHomePosition(self):
        print('Going Home')
        self.ui.initializeProgressBar.setEnabled(True)
        self.ui.initializeProgressLabel.setEnabled(True)
        self.ui.initializeProgressLabel.setText('Moving motors to Home position...')
        self.ui.initializeProgressBar.setValue(0.0)

        initialErrors: dict = {}
        totalInitialErrors: float = 0.0
        currentErrors: dict = {}
        percentToGoal: float = 0.0

        for mname in self.motorSet:
            m = self.motors[mname]
            (pos, vel, torque) = m.read_motor_measurement()
            initialErrors[mname] = pos
            totalInitialErrors += initialErrors[mname]

        while True:
            for param_i in range(len(self.motors)):
                m = self.motors[self.motorSet[param_i]]
                m.moveTo(0.0)
                time.sleep(0.2)
                app.processEvents()

                (pos, vel, torque) = m.read_motor_measurement()
                currentErrors[self.motorSet[param_i]] = pos

                percentToGoal += currentErrors[self.motorSet[param_i]]
            percentToGoal /= totalInitialErrors
            percentToGoal *= 100
            percentToGoal = 100 - percentToGoal
            self.ui.initializeProgressBar.setValue(percentToGoal)

            if percentToGoal > 99.0:
                self.ui.initializeProgressBar.setValue(100.0)
                self.ui.initializeProgressLabel.setText('All motors are at the origin now')
                break
            percentToGoal = 0.0

        for m in self.devices['motors'].values():
            self.motorGUI['currentPosLabel'][self.get_key_from_value(self.devices['motors'], m)].setText(
                '{:.2f}'.format(0.0))

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

        scale = []
        pos = [0.0, 0.0, 0.0]
        vel = [0.0, 0.0, 0.0]
        torque = [0.0, 0.0, 0.0]

        for i in range(len(self.motorSet)):
            self.devices['motors'][self.motorSet[i]].moveTo_scaled(float(targetPos[i]))
            scale.append(self.params[self.motorSet[i]]['scale'])
            self.motorGUI['currentPosLabel'][self.motorSet[i]].setText('{:.2f}'.format(float(targetPos[i])))

        while True:
            errors = 0.0
            for param_i in range(len(self.motorSet)):
                time.sleep(0.2)

                (pos[param_i], vel[param_i], torque[param_i]) = \
                    self.devices['motors'][self.motorSet[param_i]].read_motor_measurement()
                errors += pow(pos[param_i] - (float(targetPos[param_i]) * scale[param_i]), 2)

            if math.sqrt(errors) < 0.1:
                break

        for i in range(len(self.motorSet)):
            self.motorGUI['currentPosLabel'][self.motorSet[i]].setText('{:.2f}'.format(float(targetPos[i])))
        if self.subWindow.conn:
            self.subWindow.getImg(1)

    def showSubWindow(self, geometry, framesize):
        if self.subWindow_isOpen:
            self.subWindow.activateWindow()
            self.subWindow.show()
        else:
            self.subWindow.show()
            self.subWindow.move(geometry.width() / 2 - framesize.width() / 16,
                                geometry.height() / 2 - framesize.height() / 3)
            self.subWindow_isOpen = True

    def openIR(self):

        message = self.IRLight.open()
        self.devices['lights'] = self.IRLight

        self.ui.IRstateLabel.setText(message)

    def IRlightControl(self, ch, state):

        self.IRLight.set(ch, state)


    def setMultiplier(self):
        self.scriptParams.IRonMultiplier = float(self.ui.IRonMultiplier.text())
        self.scriptParams.IRoffMultiplier = float(self.ui.IRoffMultiplier.text())

    # ----- UI-related functions -----
    def GUIwhenScripting(self, bool):
        # in Robot Control Group
        for m in self.motorSet:
            self.motorGUI['exe'][m].setEnabled(bool)
            self.motorGUI['posSpin'][m].setEnabled(bool)
            self.motorGUI['speedSpin'][m].setEnabled(bool)
        self.ui.savedPosCombo.setEnabled(bool)
        self.ui.saveButton.setEnabled(bool)
        self.ui.goHomeButton.setEnabled(bool)
        self.ui.setAsHomeButton.setEnabled(bool)

        # in IR light Control Group
        self.ui.onL1Button.setEnabled(bool)
        self.ui.offL1Button.setEnabled(bool)
        self.ui.onL2Button.setEnabled(bool)
        self.ui.offL2Button.setEnabled(bool)

        # in Script Group
        self.ui.Scripting_groupBox.setEnabled(not bool)

        self.ui.continueButton.setEnabled(bool)
        self.ui.executeScript_button.setEnabled(bool)
        self.ui.selectScript_toolButton.setEnabled(bool)
        self.ui.selectBaseFolder_toolButton.setEnabled(bool)
        self.ui.renewSubFolder_toolButton.setEnabled(bool)
        self.ui.selectSubFolder_toolButton.setEnabled(bool)

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
        else:
            self.ui.manualOperation.setEnabled(False)

        if UIState.IRLIGHT in status:
            self.ui.IRlightControlGroup.setEnabled(True)
        else:
            self.ui.IRlightControlGroup.setEnabled(False)

        if UIState.SENSOR_CONNECTED in status:
            # self.ui.viewSensorWinButton.setEnabled(True)
            # self.subWindow.ui_s.setIPaddressButton.setEnabled(False)
            self.subWindow.ui_s.connectButton.setEnabled(False)
            self.subWindow.ui_s.IPlineEdit.setEnabled(False)
            self.subWindow.ui_s.disconnectButton.setEnabled(True)
            self.subWindow.ui_s.cameraControlGroup.setEnabled(True)
            self.subWindow.ui_s.laserControlGroup.setEnabled(True)
        else:
            # self.subWindow.ui_s.setIPaddressButton.setEnabled(True)
            self.subWindow.ui_s.connectButton.setEnabled(True)
            self.subWindow.ui_s.IPlineEdit.setEnabled(True)
            self.subWindow.ui_s.disconnectButton.setEnabled(False)
            self.subWindow.ui_s.cameraControlGroup.setEnabled(False)
            self.subWindow.ui_s.laserControlGroup.setEnabled(False)

        if UIState.SCRIPT in status:
            self.ui.selectScript_toolButton.setEnabled(True)
            self.ui.selectScript_toolButton_2.setEnabled(True)
            self.ui.delete2ndScriptButton.setEnabled(True)
            self.ui.selectBaseFolder_toolButton.setEnabled(True)
            self.ui.selectSubFolder_toolButton.setEnabled(True)
            self.ui.renewSubFolder_toolButton.setEnabled(True)
            self.ui.continueButton.setEnabled(True)
            self.ui.executeScript_button.setEnabled(True)
        else:
            self.ui.selectScript_toolButton.setEnabled(False)
            self.ui.selectScript_toolButton_2.setEnabled(False)
            self.ui.delete2ndScriptButton.setEnabled(False)
            self.ui.selectBaseFolder_toolButton.setEnabled(False)
            self.ui.selectSubFolder_toolButton.setEnabled(False)
            self.ui.renewSubFolder_toolButton.setEnabled(False)
            self.ui.continueButton.setEnabled(False)
            self.ui.executeScript_button.setEnabled(False)


        if UIState.SCRIPT_PROGRESS in status:
            self.ui.Scripting_groupBox.setEnabled(True)
            self.ui.stopButton.setEnabled(True)
        else:
            self.ui.Scripting_groupBox.setEnabled(False)
            self.ui.stopButton.setEnabled(False)


# ----- Scripting-related functions -----
    def updatePercentage(self):
        self.percent = self.done / self.total * 100
        # print(self.percent)
        self.ui.progressBar.setValue(self.percent)
        return self.percent

    def updateProgressLabel(self):
        self.ui.progressLabel.setText(str(self.done) + ' / ' + str(self.total))

    def interrupt(self):
        self.stopClicked = True
        # self.close()
# ==================================================================

# ----- Select machine -----
    def selectMachine(self):
        (fileName, selectedFilter) = \
            QtWidgets.QFileDialog.getOpenFileName(self, 'Select script', 'machineFiles', '*.json')

        if fileName == '':  # when cancel pressed
            pass
        else:
            self.previousMachineFilePath = fileName
            ini.updatePreviousMachineFile('data/previousMachine.ini', self.previousMachineFilePath)
            self.machineParams = read_machine_file.loadJson(self.previousMachineFilePath)

            self.ui.machineFileName_label.setText(os.path.basename(self.previousMachineFilePath))
            self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}
            self.setUIStatus(self.states)
            # self.ui.initializeButton.setEnabled(True)
# ==================================================================
    def sensorChanged(self, connected):
        print('changed')
        # if connected:
        #     self.states = {UIState.SENSOR_CONNECTED}
        #     self.setUIStatus(self.states)
        # else:
        #     self.setUIStatus(self.states)



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(':/MkECTL.png'))
    keiganWindow = Ui()
    keiganWindow.show()
    # sensorWindow = SensorWindow()
    app.exec_()

# if keiganWindow.ui.dummyMode.isEnabled():
#     keiganWindow.ui.sliderCurrentLabel.setText(keiganWindow.devices['motors']['slider'].m_posion)
