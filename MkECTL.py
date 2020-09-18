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
import pty
import MyDoubleSpinBox

import motordic
import mainwindow_ui
import execute_script
import sensors
import ini

class ScriptParams():
    def __init__(self):
        self.now = datetime.datetime.now()

        self.scriptName: str = ''
        self.baseFolderName: str = 'data'
        self.subFolderName: str = self.now.strftime('%Y%m%d_%H%M%S')
        self.isContinue = False

        self.IRonMultiplier = 1.0
        self.IRoffMultiplier = 1.0

    def renewSubFolderName(self):
        self.now = datetime.datetime.now()
        self.subFolderName = self.now.strftime('%Y%m%d_%H%M%S')

class Ui(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.ui = mainwindow_ui.Ui_mainwindow()
        self.ui.setupUi(self)
        self.scriptParams = ScriptParams()

        self.subWindow = sensors.SensorWindow()

        self.initializeProcessFlag = False

        self.ui.manualOperation.setEnabled(False)
        self.ui.IRlightControlGroup.setEnabled(False)
        self.ui.continueButton.setEnabled(False)
        self.ui.executeScript_button.setEnabled(False)

        # IR light
        self.isPortOpen = True
        self.IRport = None
        # self.openIR('/dev/ttyACM0')

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
        self.ui.initializeButton.clicked.connect(self.initializeMotors)
        self.ui.MagikEye.clicked.connect(self.demo)
        self.ui.selectScript_toolButton.clicked.connect(self.openScriptFile)
        self.ui.selectBaseFolder_toolButton.clicked.connect(self.openBaseFolder)
        self.ui.selectSubFolder_toolButton.clicked.connect(self.openSubFolder)
        self.ui.renewSubFolder_toolButton.clicked.connect(self.renewSubFolder)
        self.ui.executeScript_button.clicked.connect(lambda: self.run_script(False))
        self.ui.continueButton.clicked.connect(lambda: self.run_script(True))
        self.ui.viewSensorWinButton.clicked.connect(lambda: self.showSubWindow(self.geometry, self.framesize))
        self.ui.sliderOriginButton.clicked.connect(self.setSliderOrigin)
        self.ui.freeButton.clicked.connect(self.freeAllMotors)
        self.ui.onL1Button.clicked.connect(lambda: self.IRlightControl(1, True))
        self.ui.offL1Button.clicked.connect(lambda: self.IRlightControl(1, False))
        self.ui.onL2Button.clicked.connect(lambda: self.IRlightControl(2, True))
        self.ui.offL2Button.clicked.connect(lambda: self.IRlightControl(2, False))
        self.ui.setAsHomeButton.clicked.connect(self.setHome)
        self.ui.goHomeButton.clicked.connect(self.goHome)
        self.ui.saveButton.clicked.connect(self.savePositions)
        self.ui.GoButton.clicked.connect(self.goToSavedPositions)

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
        count += 10
        self.ui.initializeProgressBar.setValue(count)

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

        # IR light
        self.openIR('/dev/ttyACM0')

        # GUI
        print('--initialization completed--')
        self.ui.initializeProgressBar.setValue(100)
        self.ui.initializeButton.setEnabled(False)
        self.ui.initializeProgressBar.setEnabled(False)
        self.ui.initializeProgressLabel.setText('Initialized all motors')
        self.ui.manualOperation.setEnabled(True)
        self.ui.IRlightControlGroup.setEnabled(True)
        self.ui.continueButton.setEnabled(True)
        self.ui.executeScript_button.setEnabled(True)

    def setSliderOrigin(self):
        m = self.motors['slider']
        # m = self.params['slider']['cont']
        # scale = self.params['slider']['scale']
        m.speed(10.0)
        # m.maxTorque(0.5)
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

            self.motorGUI['currentPosLabel'][motorID].setText('{:.2f}'.format(motorPos))

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
        self.ui.initializeButton.setEnabled(True)
        self.ui.initializeProgressBar.setValue(0)
        self.ui.initializeProgressLabel.setText('Initializing motors...')
        self.ui.manualOperation.setEnabled(False)
        self.ui.IRlightControlGroup.setEnabled(False)
        self.ui.continueButton.setEnabled(False)
        self.ui.executeScript_button.setEnabled(False)

        QtWidgets.QMessageBox.information(self, "reboot", "All motors have been rebooted. \n"
                                                          "Please re-initialize motors to use again.")

    def changeUnitLabel(self):
        motorID = self.ui.presetMotorCombo.currentText()
        if motorID == 'slider':
            self.ui.unitLabel.setText('mm')
        elif motorID == 'pan' or 'tilt':
            self.ui.unitLabel.setText('deg')

    def openScriptFile(self):  # https://www.xsim.info/articles/PySide/special-dialogs.html#OpenFile
        (fileName, selectedFilter) = \
            QtWidgets.QFileDialog.getOpenFileName(self, 'Select script', './script/', '*.txt')

        self.ui.scriptName_label.setText(
            os.path.basename(fileName))  # https://qiita.com/inon3135/items/f8ebe85ad0307e8ddd12
        self.scriptParams.scriptName = fileName

    def openBaseFolder(self):
        fileName = \
            QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder')

        self.ui.baseFolderName_label.setText(os.path.abspath(fileName))
        self.scriptParams.baseFolderName = fileName

    def openSubFolder(self):
        fileName = \
            QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder', self.scriptParams.baseFolderName + '/')

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
            execute_script.execute_script(self.scriptParams, self.devices, self.params)

    def keyPressEvent(self, event):
        key = event.key()
        # if key == QtCore.Qt.Key_Escape:
        #     # self.close()
        #     # QtWidgets.QUndoStack.undo()
        #     self.undoValue()

    def run_script(self, isContinue):
        if isContinue:
            self.scriptParams.isContinue = True
            if self.scriptParams.subFolderName == '':
                self.openSubFolder()
            if os.path.exists(self.scriptParams.baseFolderName + '/'
                              + self.scriptParams.subFolderName + '/'
                              + 'Log.ini'):
                self.scriptParams.scriptName = ini.loadIni(
                    self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName)
                self.ui.scriptName_label.setText(os.path.basename(self.scriptParams.scriptName))
        else:
            self.scriptParams.isContinue = False

        if self.scriptParams.scriptName == '':
            self.openScriptFile()

        if not os.path.exists(self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName):
            os.makedirs(self.scriptParams.baseFolderName + '/' + self.scriptParams.subFolderName)

        self.showSubWindow(self.geometry, self.framesize)

        # GUI
        self.GUIwhenScripting(False)

        stopped = execute_script.execute_script(self.scriptParams, self.devices, self.params)

        self.GUIwhenScripting(stopped)

    def setHome(self):
        for m in self.devices['motors'].values():
            m.presetPosition(0.0)
            self.motorGUI['posSpin'][self.get_key_from_value(self.devices['motors'], m)].setValue(0.0)

            self.motorGUI['currentPosLabel'][self.get_key_from_value(self.devices['motors'], m)].setText(
                '{:.2f}'.format(0.0))

    def goHome(self):
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
        pos = self.ui.savedPosCombo.currentText().split()  # list
        for i in range(len(self.motorSet)):
            self.devices['motors'][self.motorSet[i]].moveTo_scaled(float(pos[i]))
            self.motorGUI['currentPosLabel'][self.motorSet[i]].setText('{:.2f}'.format(float(pos[i])))

    def showSubWindow(self, geometry, framesize):
        self.subWindow.show()
        self.subWindow.move(geometry.width() / 2 - framesize.width() / 16,
                            geometry.height() / 2 - framesize.height() / 3)
        self.subWindow_isOpen = True

    def openIR(self, tty):
        # https://qiita.com/macha1972/items/4869b71c14d25fa5b8f8
        try:
            self.IRport = serial.Serial(tty, 115200)
            self.isPortOpen = True
            self.devices['lights'] = self.IRport

            self.ui.IRstateLabel.setText('IR lights are ready.')
        except Exception as e:
            # QtWidgets.QMessageBox.critical(self, 'IR port open', 'Could not open port of IR lights')
            print(e)
            self.isPortOpen = False

            # https://stackoverflow.com/questions/2291772/virtual-serial-device-in-python
            master, slave = pty.openpty()
            tty_dummy = os.ttyname(slave)
            self.IRport = serial.Serial(tty_dummy)
            self.devices['lights'] = self.IRport

            self.ui.IRstateLabel.setText('Cannot open ' + tty + '. \n'
                                         + 'Using dummy serial device instead(pty).')

    def IRlightControl(self, ch, state):
        # if self.isPortOpen:
        #     cmd = ord('A') if state else ord('a')
        #     if 0 < ch < 3:
        #         cmd = cmd + ch - 1
        #     self.IRport.write(bytes([cmd]))
        # else:
        #     print('could not send serial')
        cmd = ord('A') if state else ord('a')
        if 0 < ch < 3:
            cmd = cmd + ch - 1
        self.IRport.write(bytes([cmd]))

    def setMultiplier(self):
        self.scriptParams.IRonMultiplier = float(self.ui.IRonMultiplier.text())
        self.scriptParams.IRoffMultiplier = float(self.ui.IRoffMultiplier.text())

    def GUIwhenScripting(self, bool):
        for m in self.motorSet:
            self.motorGUI['exe'][m].setEnabled(bool)
            self.motorGUI['posSpin'][m].setEnabled(bool)
            self.motorGUI['speedSpin'][m].setEnabled(bool)
        self.ui.savedPosCombo.setEnabled(bool)
        self.ui.saveButton.setEnabled(bool)
        self.ui.goHomeButton.setEnabled(bool)
        self.ui.setAsHomeButton.setEnabled(bool)
        self.ui.continueButton.setEnabled(bool)
        self.ui.executeScript_button.setEnabled(bool)

    def undoValue(self):
        # if self.state() != QtWidgets.QAbstractItemView.EditingState:
        self.motorGUI['posSpin']['slider'].QUndoStack.undo()

app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon(':/MkECTL.png'))
keiganWindow = Ui()
keiganWindow.show()
# sensorWindow = SensorWindow()
app.exec_()

# if keiganWindow.ui.dummyMode.isEnabled():
#     keiganWindow.ui.sliderCurrentLabel.setText(keiganWindow.devices['motors']['slider'].m_posion)
