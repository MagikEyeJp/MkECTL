from PyQt5 import QtWidgets, uic, QtGui, QtCore
import sys
import time
import os
import math
import re

import motordic
import mainwindow_ui
import read_script
import sensors

class Ui(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.ui = mainwindow_ui.Ui_keigan()
        self.ui.setupUi(self)

        self.subWindow = sensors.SensorWindow()  # 20200325remote

        self.initializeProcessFlag = False

        # 画面サイズを取得 (a.desktop()は QtWidgets.QDesktopWidget )  https://ja.stackoverflow.com/questions/44060/pyqt5%E3%81%A7%E3%82%A6%E3%82%A3%E3%83%B3%E3%83%89%E3%82%A6%E3%82%92%E3%82%B9%E3%82%AF%E3%83%AA%E3%83%BC%E3%83%B3%E3%81%AE%E4%B8%AD%E5%A4%AE%E3%81%AB%E8%A1%A8%E7%A4%BA%E3%81%97%E3%81%9F%E3%81%84
        a = QtWidgets.qApp
        desktop = a.desktop()
        geometry = desktop.screenGeometry()
        # ウインドウサイズ(枠込)を取得
        framesize = self.frameSize()
        # ウインドウの位置を指定
        # self.move(geometry.width() / 2 - framesize.width() / 2, geometry.height() / 2 - framesize.height() / 2)
        self.move(geometry.width() / 2 - framesize.width(), geometry.height() / 2 - framesize.height() / 2)


        # variables
        self.params = {}  # motorDic
        self.scriptName: str = ''
        self.motorSet = ['slider', 'pan', 'tilt']
        self.devices: dict = {}  # 'motors', 'lights', 'laser' etc.  # Dict of dictionaries
        self.motors: dict = {}  # 'slider', 'pan', 'tilt' (may not have to be a member val)
        self.motorGUI: dict = {}  # 'exe', 'posSpin', 'speedSpin'  # GUI objects related to motors  # Dict of dictionaries

        self.make_motorGUI()

        # connect to exeButtonClicked

        # self.ui.sliderMoveExe.clicked.connect(lambda: self.exeButtonClicked('sliderMoveExe'))
        # self.ui.panMoveExe.clicked.connect(lambda: self.exeButtonClicked('panMoveExe'))
        # self.ui.tiltMoveExe.clicked.connect(lambda: self.exeButtonClicked('tiltMoveExe'))
        for m_name in self.motorSet:
            code_exebutton: str = 'self.motorGUI[\'exe\'][\'%s\'].clicked.connect' \
                                  '(lambda: self.exeButtonClicked(self.motorGUI[\'exe\'][\'%s\'].objectName()))' \
                                  % (m_name, m_name)
            exec(code_exebutton)
        self.ui.presetExe.clicked.connect(lambda: self.exeButtonClicked('presetExe'))
        self.ui.rebootButton.clicked.connect(self.rebootButtonClicked)

        # other buttons
        self.ui.initializeButton.clicked.connect(self.initializeMotors)
        # self.ui.initializeButton.clicked.connect(self.grayOut)
        self.ui.MagikEye.clicked.connect(self.demo)
        self.ui.selectScript_toolButton.clicked.connect(self.openFile)
        self.ui.executeScript_button.clicked.connect(self.run_script)
        self.ui.viewSensorWinButton.clicked.connect(lambda: self.showSubWindow(geometry, framesize))

        self.ui.sliderOriginButton.clicked.connect(self.setSliderOrigin)
        self.ui.freeButton.clicked.connect(self.freeAllMotors)

        # Combo box event
        self.ui.presetMotorCombo.currentTextChanged.connect(self.changeUnitLabel)

        # set validator of line edit
        self.ui.presetValue.setValidator(QtGui.QDoubleValidator(-100.0, 2100.0, 2, self.ui.presetValue))

        # spinbox returnPressed

        self.ui.sliderPosSpin.setKeyboardTracking(False)
        self.ui.sliderPosSpin.valueChanged.connect(lambda: self.exeButtonClicked('sliderMoveExe'))
        self.ui.panPosSpin.setKeyboardTracking(False)
        self.ui.panPosSpin.valueChanged.connect(lambda: self.exeButtonClicked('panMoveExe'))
        self.ui.tiltPosSpin.setKeyboardTracking(False)
        self.ui.tiltPosSpin.valueChanged.connect(lambda: self.exeButtonClicked('tiltMoveExe'))

        self.ui.presetValue.returnPressed.connect(lambda: self.exeButtonClicked('presetExe'))

        # update speed
        self.ui.sliderSpeedSpin.setKeyboardTracking(False)
        self.ui.sliderSpeedSpin.valueChanged.connect(lambda: self.updateSpeed('sliderSpeedSpin'))
        self.ui.panSpeedSpin.setKeyboardTracking(False)
        self.ui.panSpeedSpin.valueChanged.connect(lambda: self.updateSpeed('panSpeedSpin'))
        self.ui.tiltSpeedSpin.setKeyboardTracking(False)
        self.ui.tiltSpeedSpin.valueChanged.connect(lambda: self.updateSpeed('tiltSpeedSpin'))


    def closeEvent(self, event):  # https://www.qtcentre.org/threads/20895-PyQt4-Want-to-connect-a-window-s-close-button
        self.deleteLater()
        event.accept()
        self.subWindow.close()  # mainwindowが閉じたらsubwindowも閉じる

    def make_motorGUI(self):  # 20200304remote
        # make dictionaries of member valuables
        exeButtons: dict = {}
        posSpinboxes: dict = {}
        speedSpinboxes: dict = {}

        for m_name in self.motorSet:
            # https://teratail.com/questions/51674
            exeButtonsCode: str = '%s[\'%s\'] = %s%s%s' % ('exeButtons', m_name, 'self.ui.', m_name, 'MoveExe')  # exeButtons[~~] = self.ui.~~MoveExe
            exec(exeButtonsCode)
            posSpinCode = '%s[\'%s\'] = %s%s%s' % ('posSpinboxes', m_name, 'self.ui.', m_name, 'PosSpin')  # posSpinboxes[~~] = self.ui.~~PosSpin
            exec(posSpinCode)
            speedSpinCode = '%s[\'%s\'] = %s%s%s' % ('speedSpinboxes', m_name, 'self.ui.', m_name, 'SpeedSpin')  # speedSpinboxes[~~] = self.ui.~~SpeedSpin
            exec(speedSpinCode)


        self.motorGUI['exe'] = exeButtons  # ex.) motorGUI['exe']['slider'] == self.ui.sliderMoveExe
        self.motorGUI['posSpin'] = posSpinboxes  # ex.) motorGUI['posSpin']['slider'] == self.ui.sliderPosSpin
        self.motorGUI['speedSpin'] = speedSpinboxes  # ex.) motorGUI['speedSpin']['slider'] == self.ui.sliderSpeedSpin

    def grayOut(self):  # for trial
        self.ui.robotControl.setEnabled(False)
        self.ui.sliderOriginButton.setEnabled(False)

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

            if p['id'] == 'slider':
                m.speed(self.ui.sliderSpeedSpin.value())
                print('slider speed  = ' + str(self.ui.sliderSpeedSpin.value()) + 'rad/s')
            elif p['id'] == 'pan':
                m.speed(self.ui.panSpeedSpin.value())
                print('pan speed = ' + str(self.ui.panSpeedSpin.value()) + 'rad/s')
            elif p['id'] == 'tilt':
                m.speed(self.ui.tiltSpeedSpin.value())
                print('tilt speed = ' + str(self.ui.tiltSpeedSpin.value()) + 'rad/s')

            self.motors[p['id']] = m    # member valuable of class

            count += 30
            time.sleep(0.2)
            self.ui.initializeProgressBar.setValue(count)

        print('--initialization completed--')
        self.ui.initializeProgressBar.setValue(100)
        self.ui.initializeButton.setEnabled(False)
        self.ui.initializeProgressLabel.setText('Initialized all motors')

        self.devices['motors'] = self.motors

    def setSliderOrigin(self):
        m = self.motors['slider']  # 20200304remote
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
        # print('FREE All Motors Button was clicked')
        # freeall.freeAllMotors()
        # m = self.params['slider']['cont']
        # for p in self.params.values():
        #     m = p['cont']
        #     m.free()

        for m in self.motors.values():
            m.free()
        QtWidgets.QMessageBox.information(self, "free", "All motors have been freed.")

        # print('--free completed--')

    def updateSpeed(self, speedSpinName):
        motorID = speedSpinName.replace('SpeedSpin', '')
        m = self.motors[motorID]
        m.speed(self.motorGUI['speedSpin'][motorID].value())

    def exeButtonClicked(self, buttonName):
        # print(buttonName)  # type->str
        # if buttonName == '.+MoveExe':  # 20200304remote
        if re.search('.+MoveExe', buttonName):
            motorID = buttonName.replace('MoveExe', '')
            m = self.motors[motorID]
            scale = self.params[motorID]['scale']
            motorPos = self.motorGUI['posSpin'][motorID].value()
            # m.speed(self.motorGUI['speedSpin'][motorID].value())
            m.moveTo(motorPos * scale)

        elif buttonName == 'presetExe':
            motorID = self.ui.presetMotorCombo.currentText()
            m = self.motors[motorID]
            # m = self.params[motorID]['cont']

            scale = self.params[motorID]['scale']
            pos = float(self.ui.presetValue.text())
            m.presetPosition(pos * scale)

            self.motorGUI['posSpin'][motorID].setValue(pos)


    def rebootButtonClicked(self):
        for m in self.motors.values():
            m.reboot()
            m.close()

        self.ui.initializeButton.setEnabled(True)
        self.ui.initializeProgressBar.setValue(0)
        self.ui.initializeProgressLabel.setText('Initializing motors...')


        QtWidgets.QMessageBox.information(self, "reboot", "All motors have been rebooted. \n"
                                                          "Please re-initialize motors to use again.")


    def changeUnitLabel(self):
        motorID = self.ui.presetMotorCombo.currentText()
        if motorID == 'slider':
            self.ui.unitLabel.setText('mm')
        elif motorID == 'pan' or 'tilt':
            self.ui.unitLabel.setText('deg')

    def openFile(self):  # https://www.xsim.info/articles/PySide/special-dialogs.html#OpenFile
        (fileName, selectedFilter) = \
            QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', './script/')

        # if fileName != "":
        #     QtWidgets.QMessageBox.information(self, "File", fileName)

        self.ui.scriptName_label.setText(os.path.basename(fileName)) # https://qiita.com/inon3135/items/f8ebe85ad0307e8ddd12
        self.scriptName = fileName

    def demo(self):
        demo_script = 'script/demo.txt'

        if not os.path.exists(demo_script):
            QtWidgets.QMessageBox.critical\
                (self, "File",
                 'Demo script doesn\'t exist. \n '
                 'Please check \" ~'
                 + os.path.abspath(os.getcwd()) + demo_script.replace("./", "/") + '\"')
            # https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory

        else:
            read_script.execute_script(demo_script, self.devices, self.params)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.close()

    def run_script(self):
        if self.scriptName == '':
            QtWidgets.QMessageBox.critical(self, "Cannot open a file", 'Please select a script.')
        else:
            read_script.execute_script(self.scriptName, self.devices, self.params)

    def setHome(self):  # 20200325remote
        for m in self.motors:
            m.presetPosition(0.0)
            self.motorGUI['posSpin'][self.get_keys_from_value(self.motors, m)].setValue(0.0)

    def goHome(self):   # 20200325remote
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

    def showSubWindow(self, geometry, framesize):
        self.subWindow.show()
        self.subWindow.move(geometry.width() / 2 - framesize.width() / 16, geometry.height() / 2 - framesize.height() / 3)


app = QtWidgets.QApplication(sys.argv)
keiganWindow = Ui()
keiganWindow.show()
# sensorWindow = SensorWindow()
app.exec_()
