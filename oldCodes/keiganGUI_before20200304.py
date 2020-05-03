from PyQt5 import QtWidgets, uic, QtGui
import sys
import time
import os
import math

import motordic
import mainwindow_ui
import read_script

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        self.ui = mainwindow_ui.Ui_keigan()
        self.ui.setupUi(self)

        self.initializeProcessFlag = False

        # connect to exeButtonClicked
        self.ui.sliderMoveExe.clicked.connect(lambda: self.exeButtonClicked('sliderMoveExe'))
        self.ui.panMoveExe.clicked.connect(lambda: self.exeButtonClicked('panMoveExe'))
        self.ui.tiltMoveExe.clicked.connect(lambda: self.exeButtonClicked('tiltMoveExe'))
        self.ui.presetExe.clicked.connect(lambda: self.exeButtonClicked('presetExe'))
        self.ui.rebootButton.clicked.connect(self.rebootButtonClicked)

        # other buttons
        self.ui.initializeButton.clicked.connect(self.initializeMotors)
        # self.ui.initializeButton.clicked.connect(self.grayOut)
        self.ui.MagikEye.clicked.connect(self.demo)
        self.ui.selectScript_button.clicked.connect(self.openFile)

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

        # variables
        self.params = {}
        self.scriptName: str = ''
        self.motorSet = ['slider', 'pan', 'tilt']

    def grayOut(self):  # for trial
        self.ui.robotControl.setEnabled(False)
        self.ui.sliderOriginButton.setEnabled(False)

    def initializeMotors(self):
        count = 0

        print('Initialize Button was clicked')
        self.ui.initializeProgressBar.setEnabled(True)
        self.ui.initilizeProgressLabel.setEnabled(True)
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

            count += 30
            time.sleep(0.5)
            self.ui.initializeProgressBar.setValue(count)

        print('--initialization completed--')
        self.ui.initializeProgressBar.setValue(100)
        self.ui.initializeButton.setEnabled(False)
        self.ui.initilizeProgressLabel.setText('Initialized all motors')


    def setSliderOrigin(self):
        m = self.params['slider']['cont']
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
        QtWidgets.QMessageBox.information(self, "Slider origin", "Current position of slider is 0 mm")

    def freeAllMotors(self):
        print('FREE All Motors Button was clicked')
        # freeall.freeAllMotors()
        # m = self.params['slider']['cont']
        for p in self.params.values():
            m = p['cont']
            m.free()
        print('--free completed--')

    def exeButtonClicked(self, buttonName):
        print(buttonName)
        if buttonName == 'sliderMoveExe':
            m = self.params['slider']['cont']
            scale = self.params['slider']['scale']
            motorPos = self.ui.sliderPosSpin.value()
            m.speed(self.ui.sliderSpeedSpin.value())
            m.moveTo(motorPos * scale)
            print('move to ' + str(motorPos) + 'mm')
        elif buttonName == 'panMoveExe':
            m = self.params['pan']['cont']
            scale = self.params['pan']['scale']
            motorPos = self.ui.panPosSpin.value()
            m.speed(self.ui.panSpeedSpin.value())
            m.moveTo(motorPos * scale)
            print('move to ' + str(motorPos) + 'deg')
        elif buttonName == 'tiltMoveExe':
            m = self.params['tilt']['cont']
            scale = self.params['tilt']['scale']
            motorPos = self.ui.tiltPosSpin.value()
            m.speed(self.ui.tiltSpeedSpin.value())
            m.moveTo(motorPos * scale)
            print('move to ' + str(motorPos) + 'deg')
        elif buttonName == 'presetExe':
            motorID = self.ui.presetMotorCombo.currentText()
            m = self.params[motorID]['cont']
            scale = self.params[motorID]['scale']
            pos = float(self.ui.presetValue.text())
            m.presetPosition(pos * scale)
            if motorID == 'slider':
                self.ui.sliderPosSpin.setValue(pos)
            elif motorID == 'pan':
                self.ui.panPosSpin.setValue(pos)
            elif motorID == 'tilt':
                self.ui.tiltPosSpin.setValue(pos)
            print('preset position of ' + motorID + ' as ' + str(pos))

    def rebootButtonClicked(self):
        motorID = self.ui.rebootMotorCombo.currentText()
        m = self.params[motorID]['cont']
        m.reboot()

        # reinitialize(まだできない)
        m.enable()
        m.interface(8)  # USB

        # self.ui.initializeButton.setEnabled(True)
        print('reboot : ' + motorID)

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
            args_hist: list = read_script.execute_script(demo_script)
            # print(args_hist)
            for args_i in range(len(args_hist)):  # https://stackoverflow.com/questions/55117021/python-warning-expected-collection-iterable-got-int-instead
                for param_i in range(args_hist[args_i].size):
                    m = self.params[self.motorSet[param_i]]['cont']
                    scale = self.params[self.motorSet[param_i]]['scale']
                    motorPos = args_hist[args_i][param_i]
                    m.speed(self.ui.sliderSpeedSpin.value())
                    print(self.motorSet[param_i] + str(motorPos))

                    m.moveTo(motorPos * scale)
                    time.sleep(0.2)

                    while True:
                        (pos, vel, torque) = m.read_motor_measurement()
                        if math.fabs(pos - motorPos * scale) < 0.1:
                            print(pos)
                            print(torque)
                            break




app = QtWidgets.QApplication(sys.argv)
window = Ui()
window.show()
app.exec_()