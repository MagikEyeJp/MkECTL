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

        # Combo Box
        self.ui_s.ISOcombo.setCurrentText(str(self.ISOvalue))
        self.ui_s.ISOcombo.currentTextChanged.connect(lambda: self.changeISO('comboBox'))

        # Line edit textChanged
        self.ui_s.IPlineEdit.setText(self.IPaddress)
        self.ui_s.IPlineEdit.textChanged.connect(self.changeIPaddress)
        self.ui_s.shutterLineEdit.setText(str(self.shutterSpeed))
        self.ui_s.shutterLineEdit.textChanged.connect(self.changeShutter)
        self.ui_s.framesLineEdit.setText(str(self.frames))
        self.ui_s.framesLineEdit.textChanged.connect(self.changeFrames)
        self.ui_s.ISOlineEdit.textChanged.connect(lambda: self.changeISO('lineEdit'))

        # set validator of line edit
        self.ui_s.shutterLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.framesLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.ISOlineEdit.setValidator(QtGui.QIntValidator(self))

        # push buttons
        self.ui_s.reconnectButton.clicked.connect(self.connectToSensor)

        # tooltip
        self.ui_s.ISOlineEdit.setToolTip('select \"Custom\" and set integer here')

        # first connect
        # self.connectToSensor()

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
        print('connectToSensor')

        # temp
        self.ui_s.sensorImage = ImageViewScene.ImageViewer()
        self.ui_s.sensorImage.setFile('GUI_icons/keigan_icon.png')
        self.ui_s.sensorImage.show()

    # def resizeEvent(self, event):   # https://gist.github.com/mieki256/1b73aae707cee97fffab544af9bc0637
    #     """ リサイズ時に呼ばれる処理 """
    #     super(SensorWindow, self).resizeEvent(event)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sensorWindow = SensorWindow()
    sensorWindow.show()
    app.exec_()