#!/usr/bin/env python3
# coding: utf-8

import datetime
import json
import os
import re
import subprocess
import sys
import time
from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from playsound import playsound

import IRLightDummy
import IRLightMkE
import IRLightNumato
import IRLightPapouch
import MyDoubleSpinBox
import execute_script
import ini
import json_IO
import mainwindow_ui
import sensors
from IMainUI import IMainUI
from KeiganRobot import KeiganRobot
from DobotRobot import DobotRobot
from SensorInfo import SensorInfo
from UIState import UIState

VERSION = '1.1.0'

class ScriptParams:
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


class Ui(QMainWindow, IMainUI):
    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.ui = mainwindow_ui.Ui_mainwindow()
        self.ui.setupUi(self)
        self.setStyleSheet("QMainWindow::separator{ background: darkgray; width: 1px; height: 1px; }")

        self.ui.MagikEye.setToolTip('MkECTL v' + VERSION + ' ©MagikEye Inc.\nPress this button to run the demo script.')
        self.scriptParams = ScriptParams()
        # self.subWindow = sensors.SensorWindow(mainUI=self)
        self.robot_connected = False

        ### docking window https://www.tutorialspoint.com/pyqt/pyqt_qdockwidget.htm
        self.sensorWindow = sensors.SensorWindow(mainUI=self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.sensorWindow)
        self.sensorWinWidth = self.sensorWindow.frameGeometry().width()
        self.sensorWinHeight = self.sensorWindow.frameGeometry().height()
        self.sensorWindow_isOpen = False

        ### detailed settings window
        self.robotSettingsWindow = None  # made in initializeMotors()

        self.ui.manualOperation.setEnabled(False)
        self.ui.SectionIRlightControl.setEnabled(False)
        self.ui.continueButton.setEnabled(False)
        self.ui.executeScript_button.setEnabled(False)
        self.ui.progressBar.setEnabled(False)

        # config file
        self.configIniFile = 'data/MkECTL.ini'

        # IR light
        self.IRLight = None

        # scripting
        self.done = 0
        self.total = 0
        self.percent = 0
        self.stopClicked = False
        self.demo_script = 'script/demo.txt'

        self.updateScriptProgress()
        self.ui.progressBar.setValue(self.percent)
        self.ui.stopButton.clicked.connect(self.interrupt)

        # 画面サイズを取得 (a.desktop()は QDesktopWidget )  https://ja.stackoverflow.com/questions/44060/pyqt5%E3%81%A7%E3%82%A6%E3%82%A3%E3%83%B3%E3%83%89%E3%82%A6%E3%82%92%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%81%AE%E4%B8%AD%E5%A4%AE%E3%81%AB%E8%A1%A8%E7%A4%BA%E3%81%97%E3%81%9F%E3%81%84
        a = qApp
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
        self.robotController = None  # instance of M_KeiganRobot
        self.motorGUI: dict = {}  # 'exe', 'posSpin', 'currentPosLabel'  # GUI objects related to motors  # Dict of dictionaries
        self.states = set()
        self.devices: dict = {}  # 'motors', 'robot', 'lights', '3Dsensors' etc.  # Dict of dictionaries

        if not os.path.exists(self.scriptParams.baseFolderName):
            os.makedirs(self.scriptParams.baseFolderName)

        self.devices['3Dsensors'] = self.sensorWindow

        self.make_motorGUI()

        # motor-related process
        for m_name in self.motorSet:
            exeButtonName: str = self.motorGUI['exe'][m_name].objectName()

            # exe buttons
            self.motorGUI['exe'][m_name].clicked.connect(partial(lambda o: o.determine(), self.motorGUI['posSpin'][m_name]))
            # position spinboxes
            self.motorGUI['posSpin'][m_name].valueChanged.connect(self.judgePresetEnable)
            self.motorGUI['posSpin'][m_name].valueDetermined.connect(partial(lambda n: self.exeButtonClicked(n), exeButtonName))

        self.ui.rebootButton.clicked.connect(self.rebootButtonClicked)

        # other buttons
        self.actionAbortRequest = False
        self.ui.actionAbortButton.clicked.connect(self.actionAbort)
        self.ui.connectButton.setEnabled(False)
        self.ui.connectButton.clicked.connect(self.connectRobot)
        self.ui.MagikEye.clicked.connect(lambda: self.demo(False))
        self.ui.getCurrentPosButton.setEnabled(False)
        self.ui.getCurrentPosButton.clicked.connect(self.captureCurrentPos)
        self.ui.selectScript_toolButton.clicked.connect(self.openScriptFile)
        self.ui.selectBaseFolder_toolButton.clicked.connect(self.openBaseFolder)
        self.ui.selectSubFolder_toolButton.clicked.connect(self.openSubFolder)
        self.ui.renewSubFolder_toolButton.clicked.connect(self.renewSubFolder)
        self.ui.executeScript_button.clicked.connect(lambda: self.run_script(False))
        self.ui.continueButton.clicked.connect(lambda: self.run_script(True))
        self.ui.viewSensorWinButton.clicked.connect(lambda: self.showSensorWindow(self.geometry, self.framesize))
        self.ui.sliderOriginButton.clicked.connect(self.initializeOrigins)
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
        self.ui.reprocessButton.clicked.connect(self.reprocesssLast)
        self.ui.postProcFileBtn.clicked.connect(self.openPostProcFile)
        self.ui.postProcEditBtn.clicked.connect(self.editPostProcParam)
        self.ui.postProcClearLogBtn.clicked.connect(self.clearPostProcLog)
        self.ui.detailedSettingsButton.clicked.connect(self.robotSettings)
        self.ui.presetButton.clicked.connect(self.presetModifiedPositions)

        # Sensor window detached
#        self.subWindow.topLevelChanged.connect(lambda toplevel: self.topLevelChanged(self.geometry, toplevel))
        self.sensorWindow.visibilityChanged.connect(lambda visible: self.visivilityChanged(self.geometry, visible))

        # set validator of line edit
        self.ui.IRonMultiplier.setValidator(QDoubleValidator(0.0, 100.0, 2, self.ui.IRonMultiplier))
        self.ui.IRoffMultiplier.setValidator(QDoubleValidator(0.0, 100.0, 2, self.ui.IRoffMultiplier))

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.periodicEvent)
        self.timer.start(1000)

    def periodicEvent(self):
        if UIState.MOTOR in self.states:
            self.getCurrentPos()

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
            if self.sensorWindow.isHidden():
                print("show subwindow")
                self.showSensorWindow(self.geometry, self.framesize)
            if self.sensorWindow.isFloating():
                print("setFloating false")
                self.sensorWindow.setFloating(False)
            self.sensorWindow.setFeatures(QDockWidget.NoDockWidgetFeatures)

            self.maxWinWidth = self.size().width()
            self.maxWinHeight = self.size().height()
        else:
            print("  not maximized")
            self.isMaxWinSize = False
            self.sensorWindow.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetFloatable)
            if self.isMaximized():
                print("  but ismMaximized")
                self.showNormal()
                self.setMinimumWidth(1040)
                self.setMaximumWidth(self.geometry.width())

    def closeEvent(self, event):
        self.deleteLater()
        event.accept()
        self.sensorWindow.close()
        exit()

    def make_motorGUI(self):
        # make dictionaries of member valuables
        exeButtons: dict = {}
        posSpinboxes: dict = {}
        currentPosLabels: dict = {}

        for m_name in self.motorSet:
            # https://teratail.com/questions/51674
            exeButtonsCode: str = '%s[\'%s\'] = %s%s%s' % (
                'exeButtons', m_name, 'self.ui.', m_name, 'MoveExe')  # exeButtons[~~] = self.ui.~~MoveExe
            exec(exeButtonsCode)
            posSpinCode = '%s[\'%s\'] = %s%s%s' % (
                'posSpinboxes', m_name, 'self.ui.', m_name, 'PosSpin')  # posSpinboxes[~~] = self.ui.~~PosSpin
            exec(posSpinCode)
            currentPosCode = '%s[\'%s\'] = %s%s%s' % (
                'currentPosLabels', m_name, 'self.ui.', m_name,
                'CurrentPos')  # currentPosLabels[~~] = self.ui.~~CurrentPos
            exec(currentPosCode)

        # print(exeButtons)
        self.motorGUI['exe'] = exeButtons  # ex.) motorGUI['exe']['slider'] == self.ui.sliderMoveExe
        self.motorGUI['posSpin'] = posSpinboxes  # ex.) motorGUI['posSpin']['slider'] == self.ui.sliderPosSpin
        self.motorGUI['currentPosLabel'] = currentPosLabels  # ex.) motorGUI['currentPosLabel']['slider'] == self.ui.sliderCurrentLabel

    def actionAbort(self):
        self.actionAbortRequest = True

    def isActionAbortRequest(self) -> bool:
        ret = self.actionAbortRequest
        self.actionAbortRequest = False
        return ret

    def connectRobot(self):
        if self.robot_connected:
            # disconnect
            if self.robotController is not None:
                self.robotController.disconnect()
                self.robotController = None

            if self.IRLight is not None:
                self.IRLight.close()
                self.IRLight = None

            self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}
            self.setUIStatus(self.states)
            self.robot_connected = False
        else:
            # initialize
            count = 0

            # GUI
            self.startAction('Connecting...')

            # Motor
            if "motors" in self.machineParams:
                if "Keigan" in self.machineParams["motors"]:
                    self.robotController = KeiganRobot(self.machineParams["motors"])
                else:
                    self.robotController = DobotRobot(self.machineParams["motors"])
            else:
                self.robotController = KeiganRobot()

            count += 10
            self.updateActionProgress(10, None, True)
            self.robotController.connect()

            self.updateActionProgress(40, 'Initializing Robot...', True)
            self.robotSettingsWindow = self.robotController.getSettingWindow()

            if self.robotController.initialize():
                self.devices['robot'] = self.robotController
                self.updateActionProgress(80, 'Initializing IRLight...', True)
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
                self.endAction('Connected.')

                self.states = {UIState.MOTOR, UIState.IRLIGHT, UIState.SCRIPT}
                self.setUIStatus(self.states)
                self.robot_connected = True
            else:
                # QMessageBox.critical(self, "Initialization Error",
                #     "Couldn\'t connect robot.\nPlease check if the robot is ready to be initialized.")
                self.abortAction('Initialization Error\nCouldn\'t connect robot.\nPlease check if the robot is ready to be initialized.')
                self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}
                self.setUIStatus(self.states)
                self.robot_connected = False

    def captureCurrentPos(self):
        pos_d = self.robotController.getPosition()
        self.updateCurrentPos(pos_d)
        self.updateTargetPosition(pos_d)
        self.judgePresetEnable()

    def getCurrentPos(self):
        pos_d = self.robotController.getPosition()
        self.updateCurrentPos(pos_d)
        self.judgePresetEnable()

    def updateCurrentPos(self, pos_d):
        if isinstance(pos_d, dict):
            for k, pos in pos_d.items():
                lb = self.motorGUI['currentPosLabel'][k]
                lb.setText('{:>8.2f}'.format(pos))
                lb.repaint()

    def allowActionAbort(self, enable):
        if enable != self.ui.actionAbortButton.isEnabled():
            self.actionAbortRequest = False
        self.ui.actionAbortButton.setEnabled(enable)

    def actionStatusCallback(self, pos_d, now, goal, allowAbort=False):
        # print("actionStatusCallBack", pos_d, now, goal, allowAbort)
        self.allowActionAbort(allowAbort)
        self.updateCurrentPos(pos_d)
        if goal != 0:
            progress = (now / goal) * 100
            if progress < 0:
                progress = 0
            elif progress > 100:
                progress = 100
            self.updateActionProgress(progress , None, None)
        app.processEvents()

    def initializeOrigins(self):
        self.startAction('Init Origins...')
        self.robotController.initializeOrigins({'slider'}, self.actionStatusCallback)
        QMessageBox.information(self, "Initialize Origin", "finished")
        self.endAction('Done')

    def freeAllMotors(self):
        self.robotController.freeMotors()
        QMessageBox.information(self, "free", "All motors have been freed.")

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
        self.robotController.presetPosition(pos_d)

    def rebootButtonClicked(self):
        self.robotController.reboot()
        self.states = {UIState.MACHINEFILE, UIState.INITIALIZE, UIState.IRLIGHT}
        self.setUIStatus(self.states)
        self.robot_connected = False
        QMessageBox.information(self, "reboot", "All motors have been rebooted. \n"
                                                          "Please re-initialize motors to use again.")

    def moveRobot(self, targetpos):
        self.startAction('Moving...')
        self.allowManualUI(False)
        isAborted = self.robotController.moveTo(targetpos, self.actionStatusCallback, False, self.isActionAbortRequest)
        self.allowActionAbort(False)
        self.allowManualUI(True)
        if isAborted:
            self.abortAction("Interrupted or Motor not moving.")
        else:
            self.endAction('Goal')
            self.updateTargetPosition(targetpos)
            if self.sensorWindow.connected:
                self.sensorWindow.prevImg(1)
        time.sleep(0.1)
        self.getCurrentPos()

    def startAction(self, action):
        self.allowActionAbort(False)
        self.updateActionProgress(0, action, True)

    def endAction(self, message):
        self.allowActionAbort(False)
        self.updateActionProgress(100, message, False)

    def abortAction(self, message):
        self.allowActionAbort(False)
        QMessageBox.critical(self, 'Aborted', message)
        self.updateActionProgress(None, None, False)

    def allowManualUI(self, enable):
        self.ui.connectButton.setEnabled(enable)
        self.ui.sliderOriginButton.setEnabled(enable)
        self.ui.freeButton.setEnabled(enable)
        self.ui.rebootButton.setEnabled(enable)
        self.ui.goHomeButton.setEnabled(enable)
        self.ui.sliderMoveExe.setEnabled(enable)
        self.ui.panMoveExe.setEnabled(enable)
        self.ui.tiltMoveExe.setEnabled(enable)
        self.ui.GoButton.setEnabled(enable)

    def updateTargetPosition(self, targetpos):
        for k in targetpos.keys():
            posspin = self.motorGUI['posSpin'].get(k)
            if type(posspin) is MyDoubleSpinBox.MyDoubleSpinBox:
                posspin.setValue(targetpos[k])
        self.judgePresetEnable()

    def updateActionProgress(self, value, text, active):
        if value is not None:
            self.ui.actionProgressBar.setValue(int(value))
            self.ui.actionProgressBar.repaint()
        if text is not None:
            self.ui.actionProgressLabel.setText(text)
            self.ui.actionProgressLabel.repaint()
        if active is not None:
            self.ui.actionProgressBar.setEnabled(active)
            self.ui.actionProgressLabel.setEnabled(active)

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
            QFileDialog.getOpenFileName(self, 'Select script', previousScriptDir, '*.txt')

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
            QFileDialog.getExistingDirectory(self, 'Select folder')

        if fileName == '':  # when cancel pressed
            pass
        else:
            self.ui.baseFolderName_label.setText(os.path.abspath(fileName))
            self.scriptParams.baseFolderName = fileName

    def openSubFolder(self):
        fileName = \
            QFileDialog.getExistingDirectory(self, 'Select folder', self.scriptParams.baseFolderName + '/')

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
            QMessageBox.critical \
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
                QMessageBox.information(self, "Finish scripting!", "All commands in \n"
                                                                   "the demo file \nhave been completed.")

        self.scriptParams.scriptName = self.ui.scriptName_label.text()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
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

                if self.ui.scriptName_label.text() != previouslyExecutedScriptName:
                    ret = QMessageBox.question(
                        self, 'continue previous script ?',
                        "The script name has changed.\n"
                        " previous one: " + previouslyExecutedScriptName + "\n"
                        " now selected: " + self.ui.scriptName_label.text() + "\n\n"
                        "Click [Yes] to continue previous script,\n"
                        "   or [No] to execute selected script from first.",
                        QMessageBox.Cancel|QMessageBox.Yes | QMessageBox.No)

                    if ret == QMessageBox.Yes:
                        self.scriptParams.scriptName = previouslyExecutedScript
                    elif ret == QMessageBox.No:
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

        self.showSensorWindow(self.geometry, self.framesize)

        # GUI
        if self.devices['3Dsensors'].connected:
            self.devices['3Dsensors'].sensorInfo.save_to_file(self.dataOutFolder() + "/sensorinfo.json")

        self.states = {UIState.SCRIPT_PROGRESS}
        self.setUIStatus(self.states)

        # execute script
        interrupted = execute_script.execute_script(self.scriptParams, self.devices, self)

        self.states = {UIState.SCRIPT, UIState.MOTOR, UIState.IRLIGHT}
        self.setUIStatus(self.states)

        if not interrupted:
            # mixer.music.play(1)
            playsound("SE/finish_chime.mp3")    # https://qiita.com/hisshi00/items/62c555095b8ff15f9dd2
            if self.ui.SectionPostProc.isChecked():
                self.doPostProc()
            QMessageBox.information(self, "Finish scripting!", "All commands in \n"
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

    def showSensorWindow(self, geometry, framesize):
        if self.sensorWindow_isOpen:
            self.sensorWindow.activateWindow()
            self.sensorWindow.show()
        else:
            self.sensorWindow.show()
            self.sensorWindow.move(geometry.width() / 2 - framesize.width() / 16,
                                   geometry.height() / 2 - framesize.height() / 3)
            self.sensorWindow_isOpen = True
        self.restoreDockWidget(self.sensorWindow)
        # self.subWindow.resize(QSize(909, 616))   # windowがfloatingしてるときはworkする。。

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
            if self.sensorWindow.isFloating() or self.sensorWindow.isHidden():
                print("isFloating:", self.sensorWindow.isFloating(), " isHidden:", self.sensorWindow.isHidden())
                self.showNormal()
                self.setMinimumWidth(540)
                self.setMaximumWidth(self.minimumWidth())
                self.setGeometry(posX, posY, self.minimumWidth(), self.size().height())
            else:
                print("  docked")
                self.showNormal()
                self.setMinimumWidth(self.minimumWidth() + self.sensorWindow.minimumWidth())
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
    def robotSettings(self):
        self.robotSettingsWindow.activateWindow()
        self.robotSettingsWindow.move(self.pos().x() + 500, self.pos().y())
        self.robotSettingsWindow.show()

    # ----- Post Process -----
    def readPostProcFile(self):
        if os.path.exists(self.previousPostProcFilePath):
            self.ui.postProcFilelabel.setText(os.path.basename(self.previousPostProcFilePath))
            with open(self.previousPostProcFilePath) as f:
                self.postproc = json.load(f)

    def openPostProcFile(self):
        (fileName, selectedFilter) = \
            QFileDialog.getOpenFileName(self, 'Select Post Process File', 'postproc', '*.json')

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

    def reprocesssLast(self):
        self.doPostProc()           # Should be error checked in the future.

    def doPostProc(self):
        infofile = self.dataOutFolder() + "/sensorinfo.json"
        if os.path.exists(infofile):
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
        else:
            QMessageBox.information(self, "post process", "sensor information file does not exist.")

    # ----- UI-related functions -----

    def setUIStatus(self, status):
        if UIState.MACHINEFILE in status:
            self.ui.selectMachineFileButton.setEnabled(True)
        else:
            self.ui.selectMachineFileButton.setEnabled(False)

        if UIState.INITIALIZE in status:
            self.ui.connectButton.setEnabled(True)
            self.ui.connectButton.setText("Connect")
            self.ui.connectButton.setStyleSheet("")
            self.ui.actionProgressBar.setEnabled(False)
            self.ui.actionProgressBar.setValue(0)
            self.ui.actionProgressLabel.setEnabled(True)
            self.ui.actionProgressLabel.setText('Push \"Connect\"')
        else:
            self.ui.connectButton.setText("Disconnect")
            self.ui.connectButton.setStyleSheet("QPushButton{background-color:red}")
            self.ui.connectButton.setEnabled(True)
            self.ui.actionProgressBar.setEnabled(False)
            self.ui.actionProgressLabel.setEnabled(False)

        if UIState.MOTOR in status:
            # self.ui.robotControl.setEnabled(True)
            self.ui.manualOperation.setEnabled(True)
            self.ui.MagikEye.setEnabled(True)
            self.ui.getCurrentPosButton.setEnabled(True)
            self.ui.detailedSettingsButton.setEnabled(True)
            self.ui.SectionRobotControl.setStyleSheet("QGroupBox{border-color:#66AAFF; border-width:2px}")
        else:
            self.ui.manualOperation.setEnabled(False)
            self.ui.MagikEye.setEnabled(False)
            self.ui.getCurrentPosButton.setEnabled(False)
            self.ui.detailedSettingsButton.setEnabled(False)
            self.ui.SectionRobotControl.setStyleSheet("")

        if UIState.IRLIGHT in status and self.IRLight.isvalid():
            self.ui.SectionIRlightControl.setEnabled(True)
            self.ui.SectionIRlightControl.setStyleSheet("QGroupBox{border-color:#66AAFF; border-width:2px}")
        else:
            self.ui.SectionIRlightControl.setEnabled(False)
            self.ui.SectionIRlightControl.setStyleSheet("")

        if UIState.SCRIPT in status:
            self.ui.selectScript_toolButton.setEnabled(True)
            self.ui.selectBaseFolder_toolButton.setEnabled(True)
            self.ui.selectSubFolder_toolButton.setEnabled(True)
            self.ui.renewSubFolder_toolButton.setEnabled(True)
            self.ui.continueButton.setEnabled(True)
            self.ui.executeScript_button.setEnabled(True)
            self.ui.SectionScript.setStyleSheet("QGroupBox{border-color:#66AAFF; border-width:2px}")
            self.ui.SectionPostProc.setEnabled(True)
        else:
            self.ui.selectScript_toolButton.setEnabled(False)
            self.ui.selectBaseFolder_toolButton.setEnabled(False)
            self.ui.selectSubFolder_toolButton.setEnabled(False)
            self.ui.renewSubFolder_toolButton.setEnabled(False)
            self.ui.continueButton.setEnabled(False)
            self.ui.executeScript_button.setEnabled(False)
            self.ui.SectionScript.setStyleSheet("")
            self.ui.SectionPostProc.setEnabled(False)

        if UIState.SCRIPT_PROGRESS in status:
            self.ui.progressBar.setEnabled(True)
            self.ui.stopButton.setEnabled(True)
            self.sensorWindow.setAllowManualOperation(False)
            self.ui.connectButton.setEnabled(False)
        else:
            self.ui.progressBar.setEnabled(False)
            self.ui.stopButton.setEnabled(False)
            self.sensorWindow.setAllowManualOperation(True)


# ----- Scripting-related functions -----
    def updatePercentage(self):
        if self.total > 0:
            self.percent = self.done / self.total * 100
        else:
            self.percent = 0.0
        # print(self.percent)
        self.ui.progressBar.setValue(self.percent)
        self.ui.progressBar.repaint()
        return self.percent

    def updateProgressLabel(self):
        self.ui.progressLabel.setText(str(self.done) + ' / ' + str(self.total))
        self.ui.progressLabel.repaint()

    def updateScriptProgress(self):
        self.updateProgressLabel()
        self.updatePercentage()

    def interrupt(self):
        self.stopClicked = True
# ==================================================================

# ----- Select machine -----
    def selectMachine(self):
        (fileName, selectedFilter) = \
            QFileDialog.getOpenFileName(self, 'Select script', 'machineFiles', '*.json')

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
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/MkECTL.png'))
    keiganWindow = Ui()
    keiganWindow.show()
    # sensorWindow = SensorWindow()
    app.exec_()

