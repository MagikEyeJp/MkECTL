# coding: utf-8
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import re
import os
from PIL import Image
import csv
import numpy as np

import socket
import SensorDevice

import sensorwindow_ui
import ImageViewScene

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
        self.conn = False
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
        self.captureDirPath = os.getcwd() + '/savedPictures'
        self.imgCounter = 0

        if not os.path.exists(self.captureDirPath):
            os.makedirs(self.captureDirPath)

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

        # Line edit returnPressed
        self.ui_s.IPlineEdit.returnPressed.connect(self.changeIPaddress)
        self.ui_s.hex4dLineEdit.returnPressed.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        # set validator of line edit
        self.ui_s.shutterLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.framesLineEdit.setValidator(QtGui.QIntValidator(self))

        # Push buttons
        self.ui_s.reconnectButton.clicked.connect(self.connectToSensor)
        self.ui_s.setIPaddressButton.clicked.connect(self.changeIPaddress)
        self.ui_s.evenLaserButton.clicked.connect(lambda: self.setLaser('0xAAAA'))
        self.ui_s.oddLaserButton.clicked.connect(lambda: self.setLaser('0x5555'))
        self.ui_s.onAllLaserButton.clicked.connect(lambda: self.setLaser('0xFFFF'))
        self.ui_s.offAllLaserButton.clicked.connect(lambda: self.setLaser('0x0000'))
        self.ui_s.setHex4dLaserButton.clicked.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        self.ui_s.prev1Button.clicked.connect(lambda: self.prevImg(1))
        self.ui_s.prevAveButton.clicked.connect(lambda: self.prevImg(self.frames))
        self.ui_s.save1Button.clicked.connect(lambda: self.saveImg(1))
        self.ui_s.saveAveButton.clicked.connect(lambda: self.saveImg(self.frames))
        self.ui_s.frameButton.clicked.connect(lambda: self.snap3D('sample.csv'))

        self.ui_s.selectDirectoryButton.clicked.connect(self.selectDirectory)
        self.ui_s.resetButton.clicked.connect(self.resetCounter)

        # Label
        # self.ui_s.CurrentLaserPattern_value.setText(str(format(0, '016b')))
        # self.ui_s.CurrentLaserPattern_value.setText('-'.join(self.binLaserPattern.replace('0b', '').zfill(16)))
        self.ui_s.CurrentLaserPattern_value.setText('0000-0000-0000-0000')
        self.ui_s.saveDirecoryName.setText(self.captureDirPath)
        self.ui_s.saveImgName.setText('img_' + str(self.imgCounter).zfill(4) + '.png')

        # image
        self.img: QtGui.QPixmap() = None
        self.imgPath = ''

        # 3D frame data
        self.csvPath = ''

        # group
        self.ui_s.cameraControlGroup.setEnabled(False)
        self.ui_s.laserControlGroup.setEnabled(False)


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
            self.sensor = SensorDevice.SensorDevice()

            self.sensor.open(self.IPaddress, self.portNum)

            # initialize values
            self.changeShutter()
            self.changeFrames()
            self.changeISO()
            self.setLaser('0x0000')

            self.ui_s.cameraStatusLabel.setText('Successfully connected to a sensor and set parameter values')

            # temp
            self.scene = ImageViewScene.ImageViewScene()
            # self.scene.setSceneRect(QtCore.QRectF(self.rect()))
            self.ui_s.sensorImage.setScene(self.scene)

            # self.ui_s.sensorImage = ImageViewScene.ImageViewer()
            # self.ui_s.sensorImage.setFile('GUI_icons/keigan_icon.png')
            # self.ui_s.sensorImage.show()
            # self.getImg(self.frames)

            self.ui_s.cameraControlGroup.setEnabled(True)
            self.ui_s.laserControlGroup.setEnabled(True)

            self.conn = True

        except Exception as e:
            self.ui_s.cameraStatusLabel.setText('!!! Sensor was not detected.')
            print(e)
            self.ui_s.cameraControlGroup.setEnabled(False)
            self.ui_s.laserControlGroup.setEnabled(False)

            self.ui_s.sensorImage.setScene(self.scene)

            self.conn = False

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
        if self.captureDirPath == '':
            QtWidgets.QMessageBox.critical(self, "Folder not found",
                                           "Please specify a folder where captured imaged to be saved.")
        else:
            pixmap = self.getImg(frames)

            saveName = self.captureDirPath + '/img_' + str(self.imgCounter).zfill(4) + '.png'
            self.ui_s.saveImgName.setText('img_' + str(self.imgCounter).zfill(4) + '.png')

            if os.path.exists(saveName):
                ans = QtWidgets.QMessageBox.question(self,'The file already exists',
                                                     "Are you sure to overwrite \n" + saveName + " ?",
                                                     QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                                     defaultButton=QtWidgets.QMessageBox.Yes)
                if ans == QtWidgets.QMessageBox.Yes:
                    pixmap.save(saveName)
                    self.imgCounter += 1
                else:
                    pass
            else:
                pixmap.save(saveName)
                self.imgCounter += 1



    def selectDirectory(self):
        self.captureDirPath = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.ui_s.saveDirecoryName.setText(self.captureDirPath)


    def getImg(self, frames):
        print('getImg', frames)
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

        return image

    def resetCounter(self):
        self.imgCounter = 0
        self.ui_s.saveImgName.setText('img_' + str(self.imgCounter).zfill(4) + '.png')

    def snap3D(self, csvName):
        frame = self.sensor.get_frame()

        uid = np.array(frame.uid).reshape(-1, 1)
        lut3d = np.array(frame.lut3d)

        data = np.hstack((uid, lut3d))

        f = open(csvName, 'w')
        writer = csv.writer(f)
        writer.writerow(['uid', 'x', 'y', 'z'])
        writer.writerows(data)
        f.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sensorWindow = SensorWindow()
    sensorWindow.show()
    app.exec_()