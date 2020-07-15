# coding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import re
import matplotlib.pyplot as plt
from PIL import Image

import socket
import SensorDevice

import sensorwindow_ui
import ImageViewScene
import execute_script

# xのあるbit位置が0か1か調べる
def getbit(x, b):
    return (x >> b) & 1

# xのある位置のbitを0または1にした値を返す(vは0または1)
def setbit(x, b, v):
    return x & ~(1 << b) | (v << b)


class SensorWindow(QtWidgets.QWidget):  # https://teratail.com/questions/118024
    def __init__(self, parent=None):
        super(SensorWindow, self).__init__(parent)

        self.ui_s = sensorwindow_ui.Ui_sensor()
        self.ui_s.setupUi(self)

        # connection
        self.conn = None    # not used
        self.sensor = SensorDevice.SensorDevice()

        # Variables (initialized with default values)
        self.IPaddress = '192.168.10.38'  # default
        self.portNum: int = 8888
        self.RPiaddress = self.IPaddress + ':' + str(self.portNum)
        self.shutterSpeed: int = 30000
        self.frames: int = 5
        self.gainiso: int = 400    # value in the list of combo box
        self.hexLaserPattern: hex = 0x0000    # Hex 4 digits
        self.binLaserPattern: bin = bin(self.hexLaserPattern)
        self.laserPattern: int = int(self.hexLaserPattern)
        self.laserX: int = 0    # laser no. when there is only one

        # Combo Box
        self.ui_s.ISOcombo.setCurrentText(str(self.gainiso))
        # self.ui_s.ISOcombo.currentTextChanged.connect(lambda: self.changeISO('comboBox'))
        self.ui_s.ISOcombo.currentTextChanged.connect(self.changeISO)
        self.ui_s.ISOcombo.setValidator(QtGui.QIntValidator(self))

        # Check Box
        self.ui_s.hex4dCheckBox.stateChanged.connect(self.laser_custom)

        # Line edit textChanged
        self.ui_s.IPlineEdit.setText(self.RPiaddress)
        # self.ui_s.IPlineEdit.textChanged.connect(self.changeIPaddress)
        self.ui_s.shutterLineEdit.setText(str(self.shutterSpeed))
        self.ui_s.shutterLineEdit.textChanged.connect(self.changeShutter)
        self.ui_s.framesLineEdit.setText(str(self.frames))
        self.ui_s.framesLineEdit.textChanged.connect(self.changeFrames)
        # self.ui_s.ISOlineEdit.textChanged.connect(lambda: self.changeISO('lineEdit'))

        # Line edit returnPressed
        self.ui_s.IPlineEdit.returnPressed.connect(self.changeIPaddress)
        self.ui_s.hex4dLineEdit.returnPressed.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        # set validator of line edit
        self.ui_s.shutterLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.framesLineEdit.setValidator(QtGui.QIntValidator(self))
        # self.ui_s.ISOlineEdit.setValidator(QtGui.QIntValidator(self))

        # Push buttons
        self.ui_s.reconnectButton.clicked.connect(self.connectToSensor)
        self.ui_s.setIPaddressButton.clicked.connect(self.changeIPaddress)
        self.ui_s.evenLaserButton.clicked.connect(lambda: self.setLaser('0xAAAA'))
        self.ui_s.oddLaserButton.clicked.connect(lambda: self.setLaser('0x5555'))
        self.ui_s.onAllLaserButton.clicked.connect(lambda: self.setLaser('0xFFFF'))
        self.ui_s.offAllLaserButton.clicked.connect(lambda: self.setLaser('0x0000'))
        self.ui_s.setHex4dLaserButton.clicked.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        self.ui_s.prev1Button.clicked.connect(lambda: self.saveImg(1))
        self.ui_s.prevAveButton.clicked.connect(lambda: self.saveImg(self.frames))
        self.ui_s.save1Button.clicked.connect(lambda: self.saveImg(1))
        self.ui_s.saveAveButton.clicked.connect(lambda: self.saveImg(self.frames))

        # Label
        # self.ui_s.CurrentLaserPattern_value.setText(str(format(0, '016b')))
        # self.ui_s.CurrentLaserPattern_value.setText('-'.join(self.binLaserPattern.replace('0b', '').zfill(16)))
        self.ui_s.CurrentLaserPattern_value.setText('0000-0000-0000-0000')

        # tooltip
        # self.ui_s.ISOlineEdit.setToolTip('select \"Custom\" and set integer here')

        # image
        self.img: QtGui.QPixmap() = None
        self.imgPath = ''

        # first connect
#        self.connectToSensor()


    def changeIPaddress(self):
        self.RPiaddress = self.ui_s.IPlineEdit.text()
        if ':' in self.RPiaddress:
            # https://teratail.com/questions/61914
            pattern = "(.*):(.*)"
            d = re.search(pattern, self.RPiaddress)
            self.IPaddress = d.group(1)
            self.portNum = int(d.group(2))
        else:
            self.IPaddress = self.RPiaddress

        self.connectToSensor()

    def changeShutter(self):
        if self.ui_s.shutterLineEdit.text() == '':
            pass
        else:
            self.shutterSpeed = int(self.ui_s.shutterLineEdit.text())
            # print(self.shutterSpeed)
            try:
                self.sensor.set_shutter(self.shutterSpeed)
                self.ui_s.cameraStatusLabel.setText('Set shutter speed as ' + str(self.shutterSpeed))

            except Exception:
                self.ui_s.cameraStatusLabel.setText('Sensor is not connected.')


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
                self.gainiso = int(self.ui_s.ISOcombo.currentText())
                self.ui_s.ISOlineEdit.setEnabled(False)
                # print(self.gainiso)

        elif valueFromX == 'lineEdit':
            if self.ui_s.ISOlineEdit.text() == "":
                pass
            else:
                self.gainiso = int(self.ui_s.ISOlineEdit.text())
                # print(self.gainiso)

    def changeISO(self):
        if self.ui_s.ISOcombo.currentText() == "":
            pass
        else:
            self.gainiso = int(self.ui_s.ISOcombo.currentText())
            # print('iso: ' + str(self.gainiso))

            try:
                self.sensor.set_gainiso(self.gainiso)
                self.ui_s.cameraStatusLabel.setText('Set ISO as ' + str(self.gainiso))

            except Exception:
                self.ui_s.cameraStatusLabel.setText('Sensor is not connected.')

    def connectToSensor(self):
        # connect to sensors and display again
        # self.sensor = SensorDevice.SensorDevice()

        try:
            # 時間がかかる 特にreconnect
            # self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.conn.connect((self.IPaddress, self.portNum))

            self.sensor.close()   # for when reconnecting

            self.sensor.open(self.IPaddress, self.portNum)
            self.ui_s.cameraStatusLabel.setText('Successfully connected to a sensor')

        except Exception as e:
            self.ui_s.cameraStatusLabel.setText('!!! Sensor was not detected.')

        # self.sensor.get_image(1)    # might be skipped

        # temp
        self.scene = ImageViewScene.ImageViewScene()
        # self.scene.setSceneRect(QtCore.QRectF(self.rect()))
        self.ui_s.sensorImage.setScene(self.scene)
        # self.img = self.scene.setFile('script/M_TOF_sample_image.png')  # これをget_imageのものにしたい。もしくはこの処理はここではskip

        # self.ui_s.sensorImage = ImageViewScene.ImageViewer()
        # self.ui_s.sensorImage.setFile('GUI_icons/keigan_icon.png')
        # self.ui_s.sensorImage.show()
        self.getImg(self.frames)


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
        if len(hex4d) != 2 + 4:
            QtWidgets.QMessageBox.critical(self, "Hex 4 digits", "Please type a 4-digit number in base 16 system.")
        else:
            # https://stackoverflow.com/questions/21879454/how-to-convert-a-hex-string-to-hex-number
            self.hexLaserPattern = hex(int(hex4d, 16))
            self.binLaserPattern = bin(int(hex4d, 16))
            self.laserPattern = int(hex4d, 16)
            laserpattern_print = self.binLaserPattern.replace('0b', '').zfill(16)
            laserpattern_print = laserpattern_print[::-1]
            laserpattern_print_list = [laserpattern_print[:4], laserpattern_print[4:8], laserpattern_print[8:12], laserpattern_print[12:]]
            laserpattern_print = ''
            for i in range(len(laserpattern_print_list)):
                laserpattern_print += laserpattern_print_list[i] + '-'
            laserpattern_print = laserpattern_print[:-1]    # https://techracho.bpsinc.jp/baba/2010_04_21/1409
            # self.ui_s.CurrentLaserPattern_value.setText('-'.join(laserpattern_print[::-1]))
            # https://qiita.com/Hawk84/items/ecd0c7239e490ea22308   https://note.nkmk.me/python-string-concat/
            self.ui_s.CurrentLaserPattern_value.setText(laserpattern_print)
            self.sensor.set_lasers(self.laserPattern)

            # for i in range(16):
            #     print(getbit(self.decLaserPattern, i))
            #     print(setbit(self.decLaserPattern, i, int(laserpattern_print[15-i])))

    def prevImg(self, frames):
        self.getImg(frames)

    def saveImg(self, frames):
        # self.ui_s.sensorImage.grab().save('imgs/QImage.png')    # https://qiita.com/akegure/items/0bce65da71e64728a307
        # self.img.save('imgs/QPixmap.png')

        self.getImg(frames)
        ### add save process



    def getImg(self, frames):
        img = self.sensor.get_image(frames)
        # print(img)
        img.format = "PNG"
        img2 = img.get_image()
        image = QtGui.QImage(img2, len(img2[0]), len(img2), QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap(image)
        # print(type(image))
        # print(type(img2))
        # img3 = Image.new('L', (len(img2[0]), len(img2)))
        # img3.show()

        self.scene.setPixMap(pixmap)

        # self.ui_s.sensorImage.setFixedSize(len(img2[0]), len(img2))
        # self.ui_s.sensorImage.resize(pixmap.size())
        self.ui_s.sensorImage.setBaseSize(len(img2[0]), len(img2))
        self.ui_s.sensorImage.setSceneRect(0, 0, len(img2[0]), len(img2))
        self.ui_s.sensorImage.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        # self.scene.fitImage()

        self.ui_s.sensorImage.show()




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sensorWindow = SensorWindow()
    sensorWindow.show()
    app.exec_()