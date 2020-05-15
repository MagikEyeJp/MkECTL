from PyQt5 import QtWidgets, QtGui, QtCore
import sys

import sensorwindow_ui
import ImageViewScene

class SensorWindow(QtWidgets.QWidget):  # https://teratail.com/questions/118024
    def __init__(self, parent=None):
        super(SensorWindow, self).__init__(parent)

        self.ui_s = sensorwindow_ui.Ui_sensor()
        self.ui_s.setupUi(self)

        # Variables (initialized with default values)
        self.IPaddress = '192.168.10.123:8888'
        self.shutterSpeed: int = 30000
        self.frames: int = 5
        self.ISOvalue: int = 400    # value in the list of combo box
        self.hexLaserPattern: hex = 0x0000    # Hex 4 digits
        self.binLaserPattern: bin = bin(self.hexLaserPattern)

        # Combo Box
        self.ui_s.ISOcombo.setCurrentText(str(self.ISOvalue))
        self.ui_s.ISOcombo.currentTextChanged.connect(lambda: self.changeISO('comboBox'))

        # Check Box
        self.ui_s.hex4dCheckBox.stateChanged.connect(self.laser_custom)

        # Line edit textChanged
        self.ui_s.IPlineEdit.setText(self.IPaddress)
        self.ui_s.IPlineEdit.textChanged.connect(self.changeIPaddress)
        self.ui_s.shutterLineEdit.setText(str(self.shutterSpeed))
        self.ui_s.shutterLineEdit.textChanged.connect(self.changeShutter)
        self.ui_s.framesLineEdit.setText(str(self.frames))
        self.ui_s.framesLineEdit.textChanged.connect(self.changeFrames)
        self.ui_s.ISOlineEdit.textChanged.connect(lambda: self.changeISO('lineEdit'))

        # Line edit returnPressed
        self.ui_s.hex4dLineEdit.returnPressed.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))


        # set validator of line edit
        self.ui_s.shutterLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.framesLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.ISOlineEdit.setValidator(QtGui.QIntValidator(self))

        # Push buttons
        self.ui_s.reconnectButton.clicked.connect(self.connectToSensor)
        self.ui_s.setHex4dLaserButton.clicked.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        # Label
        # self.ui_s.CurrentLaserPattern_value.setText(str(format(0, '016b')))
        self.ui_s.CurrentLaserPattern_value.setText(self.binLaserPattern.replace('0b', '').zfill(16))

        # tooltip
        self.ui_s.ISOlineEdit.setToolTip('select \"Custom\" and set integer here')

        # first connect
        self.connectToSensor()

    def changeIPaddress(self):
        self.IPaddress = self.ui_s.IPlineEdit.text()
        # print(self.IPaddress)

    def changeShutter(self):
        if self.ui_s.shutterLineEdit.text() == "":
            pass
        else:
            self.shutterSpeed = int(self.ui_s.shutterLineEdit.text())
            # print(self.shutterSpeed)

    def changeFrames(self):
        if self.ui_s.framesLineEdit.text() == "":
            pass
        else:
            self.frames = int(self.ui_s.framesLineEdit.text())
            # print(self.frames)

    def changeISO(self, valueFromX):
        if valueFromX == 'comboBox':
            if self.ui_s.ISOcombo.currentText() == "Custom":
                self.ui_s.ISOlineEdit.setEnabled(True)
            else:
                self.ISOvalue = int(self.ui_s.ISOcombo.currentText())
                self.ui_s.ISOlineEdit.setEnabled(False)
                print(self.ISOvalue)

        elif valueFromX == 'lineEdit':
            if self.ui_s.ISOlineEdit.text() == "":
                pass
            else:
                self.ISOvalue = int(self.ui_s.ISOlineEdit.text())
                print(self.ISOvalue)

    def connectToSensor(self):
        # connect to sensor and display again
        # print('connectToSensor')

        # temp
        self.scene = ImageViewScene.ImageViewScene()
        # self.scene.setSceneRect(QtCore.QRectF(self.rect()))
        self.ui_s.sensorImage.setScene(self.scene)
        self.scene.setFile('script/M_TOF_sample_image.png')

        # self.ui_s.sensorImage = ImageViewScene.ImageViewer()
        # self.ui_s.sensorImage.setFile('GUI_icons/keigan_icon.png')
        self.ui_s.sensorImage.show()

    # def resizeEvent(self, event):   # https://gist.github.com/mieki256/1b73aae707cee97fffab544af9bc0637
    #     """ リサイズ時に呼ばれる処理 """
    #     super(SensorWindow, self).resizeEvent(event)

    def laser_custom(self):
        if self.ui_s.hex4dCheckBox.isChecked():
            self.ui_s.hex4dLineEdit.setEnabled(True)
            self.ui_s.setHex4dLaserButton.setEnabled(True)
        else:
            self.ui_s.hex4dLineEdit.setEnabled(False)
            self.ui_s.setHex4dLaserButton.setEnabled(False)

    def setLaser(self, hex4d):
        if len(hex4d) != 4:
            QtWidgets.QMessageBox.critical(self, "Hex 4 digits", "Please type a 4-digit number in base 16 system.")
        else:
            # temp
            self.hexLaserPattern = hex(int(hex4d, 16))
            # print(self.hexLaserPattern)
            # print(type(self.hexLaserPattern))
            self.binLaserPattern = bin(int(hex4d, 16))
            self.ui_s.CurrentLaserPattern_value.setText(self.binLaserPattern.replace('0b', '').zfill(16))




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sensorWindow = SensorWindow()
    sensorWindow.show()
    app.exec_()