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

import IRobotController
import IRLight
from MachineBuilder import Machine, MachineBuilder

from MyDoubleSpinBox import MyDoubleSpinBox
import execute_script
import ini
import json_IO
import mainwindow_ui
import sensors
from IMainUI import IMainUI
from SensorInfo import SensorInfo
from UIState import UIState

VERSION = '1.2.0beta'

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

class UiAxis:
    def __init__(self, name: str, unit: str, step: float, minvalue: float = -10000.0, maxvalue: float = 10000.0):
        self.name = name
        self.unit = unit
        self.step = step
        self.min = minvalue
        self.max = maxvalue
        self.currentLabel = None
        self.spinbox = None
        self.execButton = None

class Ui(QMainWindow, IMainUI):

    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.ui = mainwindow_ui.Ui_mainwindow()
        self.ui.setupUi(self)
        self.setStyleSheet("QMainWindow::separator{ background: darkgray; width: 1px; height: 1px; }")

        self.isinitialized = False
        self.initialContentSize = self.ui.scrollAreaWidgetContents.size()
        self.initialSectionRobotSize = self.ui.SectionRobotControl.size()
        self.initialManualOperationSize = self.ui.manualOperation.size()
        self.initialPosControlSize = self.ui.posControlFrame.size()
        self.ui.MagikEye.setToolTip('MkECTL v' + VERSION + ' ©MagikEye Inc.\nPress this button to run the demo script.')
        self.scriptParams = ScriptParams()
        self.robot_connected = False
        self.uiaxes = []
        self.machine = None

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
        self.ui.progressBar.setValue(int(self.percent))
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
        self.robotController = None  # instance of M_KeiganRobot
        self.states = set()

        if not os.path.exists(self.scriptParams.baseFolderName):
            os.makedirs(self.scriptParams.baseFolderName)

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
        self.ui.initializeOriginButton.clicked.connect(self.initializeOrigins)
        self.ui.freeButton.clicked.connect(self.freeAllMotors)
        self.ui.rebootButton.clicked.connect(self.rebootButtonClicked)
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

        self.ini = ini.Ini()
        # before Initialize
        self.restoreConfig()

        self.machineParams = {}
        self.previousMachineFilePath = self.ini.getPreviousMachineFile()
        if self.previousMachineFilePath is not None:
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
            self.previousPostProcFilePath = self.ini.getPreviousPostProcFile()
            self.readPostProcFile()

    def showEvent(self, event: QShowEvent):
        if event.spontaneous():
            return
        if self.isinitialized:
            return
        self.isinitialized = True
        print("UI Initialized.")
        print("posControlFrame size", self.ui.posControlFrame.size())

    # def forceUpdate(self, widget: QWidget):
    #     for child in widget.children():
    #         if child.isWidgetType():
    #             self.forceUpdate(child)
    #     if widget.layout() is not None:
    #         self.invalidateLayout(widget.layout())
    #
    # def invalidateLayout(self, layout: QLayout):
    #     for i in range(layout.count()):
    #         item = layout.itemAt(i)
    #         if (item.layout() is not None):
    #             self.invalidateLayout(item.layout())
    #         else:
    #             item.invalidate()
    #     layout.invalidate()
    #     layout.activate()


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

    @staticmethod
    def clearLayout(layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().setParent(None)
                    # child.widget().deleteLater()
                elif child.layout() is not None:
                    clearLayout(child.layout())
                    child.layout().setParent(None)
                    # child.layout().deleteLater()

    def make_motorGUI(self):
        self.clearLayout(self.ui.posControlLayout)

        self.uiaxes = []
        for a in self.machine.axes:
            axis = UiAxis(a.name, a.unit, a.step, a.min, a.max)
            self.uiaxes.append(axis)

        parent = self.ui.manualOperation
        layout = self.ui.posControlLayout
        layout.setColumnStretch(0, 1)   # name
        layout.setColumnStretch(1, 1)   # current pos
        layout.setColumnStretch(2, 1)   # target pos
        layout.setColumnStretch(3, 0)   # exec button
        icon = QIcon()
        icon.addPixmap(QPixmap(":/GUI_icons/exec.png"), QIcon.Normal, QIcon.Off)
        for i, axis in enumerate(self.uiaxes):
            row = i * 2
            label = QLabel(parent)
            label.setText(axis.name + " [" + axis.unit + "]")
            label.setFixedHeight(24)
            layout.addWidget(label, row, 0)
            current = QLabel(parent)
            current.setText("0.00")
            current.setFixedSize(90, 24)
            current.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            layout.addWidget(current, row, 1, Qt.AlignCenter)
            axis.currentLabel = current

            spinbox = MyDoubleSpinBox(parent)
            spinbox.setKeyboardTracking(True)
            spinbox.setDecimals(2)
            spinbox.setValue(0.00)
            spinbox.setAlignment(Qt.AlignRight)
            spinbox.setFixedSize(90, 24)
            spinbox.setMinimum(axis.min)
            spinbox.setMaximum(axis.max)
            spinbox.setSingleStep(axis.step)
            spinbox.setStepType(MyDoubleSpinBox.DefaultStepType)
            spinbox.valueChanged.connect(self.judgePresetEnable)
            spinbox.valueDetermined.connect(partial(self.exeButtonClicked, axis))
            layout.addWidget(spinbox, row, 2, Qt.AlignCenter)
            axis.spinbox = spinbox

            button = QPushButton(parent)
            button.setText("")
            button.setFixedSize(QSize(24, 24))
            button.setIcon(icon)
            button.setAutoDefault(False)
            button.clicked.connect(partial(self.exeButtonClicked, axis))
            axis.execButton = button
            layout.addWidget(button, row, 3, Qt.AlignCenter)

            if i < len(self.uiaxes) - 1:
                line = QFrame(parent, Qt.Window)
                line.setGeometry(QRect(0, 0, 100, 0))
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                layout.addWidget(line, row+1, 0, 1, 4)

        spacer = QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout.addItem(spacer)
        self.ui.posControlFrame.setFixedHeight(len(self.uiaxes)*32 + 8)
        self.ui.posControlFrame.updateGeometry()
        sizediff = self.ui.posControlFrame.size() - self.initialPosControlSize
        print("sizediff:", sizediff)
        self.ui.manualOperation.setMinimumHeight(self.initialManualOperationSize.height() + sizediff.height())
        self.ui.SectionRobotControl.setMinimumHeight(self.initialSectionRobotSize.height() + sizediff.height())

        prev = None
        for axis in self.uiaxes:
            w = axis.spinbox
            if prev is not None:
                self.setTabOrder(prev, w)
            prev = w

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
            self.startAction('Connecting...')

            # build machine
            if self.machine is not None:
                self.robotController = self.machine.robot
                self.IRLight = self.machine.light

                self.updateActionProgress(10, 'Connecting Robot...', True)
                self.robotController.connect()

                self.updateActionProgress(40, 'Initializing Robot...', True)
                self.robotSettingsWindow = self.robotController.getSettingWindow()

            if self.robotController.initialize():
                self.updateActionProgress(80, 'Initializing IRLight...', True)
                # IR light
                self.openIR()

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
            for axis in self.uiaxes:
                if axis.name in pos_d.keys():
                    lb = axis.currentLabel
                    lb.setText('{:>8.2f}'.format(pos_d[axis.name]))
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
        self.robotController.initializeOrigins(None, self.actionStatusCallback)
        QMessageBox.information(self, "Initialize Origin", "finished")
        self.endAction('Done')

    def freeAllMotors(self):
        self.robotController.freeMotors()
        QMessageBox.information(self, "free", "All motors have been freed.")

    def exeButtonClicked(self, axis: UiAxis):
        self.judgePresetEnable()
        targetPos_d = {axis.name: axis.spinbox.value()}
        self.updateTargetPosition(targetPos_d)
        self.moveRobot(targetPos_d)

    def judgePresetEnable(self):
        modified = False
        for axis in self.uiaxes:
            if axis.spinbox.isModified():
                modified = True
                break
        self.ui.presetButton.setEnabled(modified)

    def presetModifiedPositions(self):
        for axis in self.uiaxes:
            if axis.spinbox.isModified():
                pos_d = {axis.name: axis.spinbox.value()}
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
        isAborted = self.robotController.moveTo(targetpos, False, self.actionStatusCallback, self.isActionAbortRequest)
        self.allowActionAbort(False)
        self.allowManualUI(True)
        if isAborted:
            self.abortAction("Interrupted or Motor not moving.")
        else:
            self.endAction('Goal')
            # self.updateTargetPosition(targetpos)
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
        self.ui.initializeOriginButton.setEnabled(enable)
        self.ui.freeButton.setEnabled(enable)
        self.ui.rebootButton.setEnabled(enable)
        self.ui.goHomeButton.setEnabled(enable)
        self.ui.GoButton.setEnabled(enable)
        for axis in self.uiaxes:
            axis.execButton.setEnabled(enable)
            axis.spinbox.allowDetermine(enable)

    def updateTargetPosition(self, targetpos):
        for axis in self.uiaxes:
            if axis.name in targetpos.keys():
                axis.spinbox.setValue(targetpos[axis.name])
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
        previousScriptDir = './script/'
        previousScriptPath = self.ini.getPreviousScriptPath()
        if previousScriptPath is not None:
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
            self.ini.updatePreviousScriptPath(fileName)

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

            interrupted = execute_script.execute_script(self.scriptParams, {'robot': self.robotController,
                                                                            'lights': self.IRLight,
                                                                            '3Dsensors': self.sensorWindow}, self, True)

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

                previouslyExecutedScriptName = os.path.basename(self.ini.loadIni(
                    self.dataOutFolder()))
                # previouslyExecutedScriptDir = os.path.dirname(ini.loadIni(
                #     self.dataOutFolder()))
                previouslyExecutedScript = self.ini.loadIni(
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
        if self.sensorWindow.connected:
            self.sensorWindow.sensorInfo.save_to_file(self.dataOutFolder() + "/sensorinfo.json")

        self.states = {UIState.SCRIPT_PROGRESS}
        self.setUIStatus(self.states)

        # execute script
        interrupted = execute_script.execute_script(self.scriptParams,
                                                    {'robot': self.robotController,
                                                     'lights': self.IRLight,
                                                     '3Dsensors': self.sensorWindow}, self)

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
        targetPos_d = {}
        for axis in self.uiaxes:
            targetPos_d[axis.name] = 0.0
        self.presetPositions(targetPos_d)

    def goToHomePosition(self):
        targetPos_d = {}
        for axis in self.uiaxes:
            targetPos_d[axis.name] = 0.0
        self.updateTargetPosition(targetPos_d)
        self.moveRobot(targetPos_d)

    def savePositions(self):
        save_name = ''
        for axis in self.uiaxes:
            save_name += str('{:.2f}'.format(axis.spinbox.value())) + ' '
            save_name.strip()  # https://itsakura.com/python-strip#s2
        if save_name not in [self.ui.savedPosCombo.itemText(i) for i in range(
                self.ui.savedPosCombo.count())]:  # https://stackoverflow.com/questions/7479915/getting-all-items-of-qcombobox-pyqt4-python
            self.ui.savedPosCombo.addItem(save_name)
        print(save_name)

    def goToSavedPositions(self):
        targetPos = self.ui.savedPosCombo.currentText().split()  # list
        targetPos_d = {}
        for i, axis in enumerate(self.uiaxes):
            targetPos_d[axis.name] = float(targetPos[i])
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
        self.ui.IRstateLabel.setText(message)

    def IRlightControl(self, ch, state):
        self.IRLight.set(ch, state)

    @staticmethod
    def toFloat(text, default):
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
            self.ini.updatePreviousPostProcFile(self.configIniFile, self.previousPostProcFilePath)
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
        self.ui.progressBar.setValue(int(self.percent))
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
            self.ini.updatePreviousMachineFile(filename)
            self.ui.machineFileName_label.setText(os.path.basename(filename))

        self.machine = MachineBuilder.build(self.machineParams)
        if self.machine is not None:
            self.make_motorGUI()
            self.states = {UIState.MACHINEFILE, UIState.INITIALIZE}
        else:
            self.states = {UIState.MACHINEFILE}

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

