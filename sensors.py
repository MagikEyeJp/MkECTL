# coding: utf-8
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget
import sys
import re
import os
import datetime
import numpy as np
from timeout_decorator import TimeoutError
import threading
import discoverdevices
import SensorDevice
# import sensorwindow_ui
import sensorwindow_dock_ui
from IMainUI import IMainUI
import PopupList
import csv
from SensorInfo import SensorInfo
import subprocess

app = QtWidgets.qApp

from qtutils import inmain

# xのあるbit位置が0か1か調べる
def getbit(x, b):
    return (x >> b) & 1

# xのある位置のbitを0または1にした値を返す(vは0または1)
def setbit(x, b, v):
    return x & ~(1 << b) | (v << b)

class GetImageThread(threading.Thread):
    def __init__(self, sensor, callback):
        super().__init__()
        self.started = threading.Event()
        self.ended = True
        self.alive = True
        self.daemon = True  # https://teratail.com/questions/76909
        self.start()
        # self.mainThread = SensorWindow()
        # self.sensor = SensorDevice.SensorDevice()
        self.sensor = sensor
        self.callback = callback
        self.image = None
        self.pixmap = None
        self.frame = 1
        print("thread created")

    # https://qiita.com/BlueSilverCat/items/44a0a2a3c45fc3e88b19
    def __del__(self):
        self.kill()

    def begin(self, frame):
        # print("begin")
        self.frame = frame
        self.started.set()
        self.ended = False

    def end(self):
        self.started.clear()
        # print("end")
        self.ended = True

    def kill(self):
        # print("kill")
        self.started.set()
        self.alive = False
        self.join()
        print("thread killed")

    def change_frame(self, frame):
        self.frame = frame

    def run(self):
        # i = 0
        while self.alive:
            self.started.wait()
            # i += 1
            # print("{}\r".format(i), end="")
            img = self.sensor.get_image(self.frame)
            # print(self.sensor)
            # print(img)
            img.format = "PNG"
            img2 = img.get_image()
            self.image = QtGui.QImage(img2, len(img2[0]), len(img2), QtGui.QImage.Format_Grayscale8)
            self.pixmap = QtGui.QPixmap(self.image)
            inmain(self.callback, self.pixmap, self.image)


class SensorWindow(QtWidgets.QDockWidget):  # https://teratail.com/questions/118024
    def __init__(self, parent=None, mainUI:IMainUI=None):
        super(SensorWindow, self).__init__(parent)
        # print(mainUI)
        # mainUI.sensorChanged()
        self.mainUI = mainUI

        # self.ui_s = sensorwindow_ui.Ui_sensor()
        self.ui_s = sensorwindow_dock_ui.Ui_sensor()
        self.ui_s.setupUi(self)

        # connection
        self.conn = False
        self.sensor = SensorDevice.SensorDevice()
        self.sensorInfo = SensorInfo()
        # print(self.sensor)

        # thread
        self.getImg_thread = None

        # Variables (initialized with default values)
        self.IPaddress = '127.0.0.1'  # default
        self.portNum: int = 8888
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
        self.ui_s.gridTypeCombo.setCurrentText(self.ui_s.sensorImage.gridParam.gridType)
        self.ui_s.gridTypeCombo.currentTextChanged.connect(self.showGrid)
        self.ui_s.gridColorCombo.setCurrentText(self.ui_s.sensorImage.gridParam.color)
        self.ui_s.gridColorCombo.currentTextChanged.connect(self.showGrid)

        # Check Box
        self.ui_s.hex4dCheckBox.stateChanged.connect(self.laser_custom)

        # set validator of line edit
        self.ui_s.shutterLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.framesLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.xLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.yLineEdit.setValidator(QtGui.QIntValidator(self))
        self.ui_s.xOffsetLineEdit.setValidator(QtGui.QDoubleValidator(self))
        self.ui_s.yOffsetLineEdit.setValidator(QtGui.QDoubleValidator(self))
        self.ui_s.rotLineEdit.setValidator(QtGui.QDoubleValidator(self))
        self.ui_s.alphaLineEdit.setValidator(QtGui.QIntValidator(0, 100, self))

        # Line edit textChanged
        # self.ui_s.IPComboBox.textChanged.connect(self.changeIPaddress)
        self.ui_s.shutterLineEdit.setText(str(self.shutterSpeed))
        self.ui_s.shutterLineEdit.textChanged.connect(self.changeShutter)
        self.ui_s.framesLineEdit.setText(str(self.frames))
        self.ui_s.framesLineEdit.textChanged.connect(self.changeFrames)
        self.ui_s.xLineEdit.setText(str(self.ui_s.sensorImage.gridParam.lines_x))
        self.ui_s.xLineEdit.textChanged.connect(self.showGrid)
        self.ui_s.yLineEdit.setText(str(self.ui_s.sensorImage.gridParam.lines_y))
        self.ui_s.yLineEdit.textChanged.connect(self.showGrid)
        self.ui_s.xOffsetLineEdit.setText(str(self.ui_s.sensorImage.gridParam.offset_x))
        self.ui_s.xOffsetLineEdit.textChanged.connect(self.showGrid)
        self.ui_s.yOffsetLineEdit.setText(str(self.ui_s.sensorImage.gridParam.offset_y))
        self.ui_s.yOffsetLineEdit.textChanged.connect(self.showGrid)
        self.ui_s.rotLineEdit.setText(str(self.ui_s.sensorImage.gridParam.rot))
        self.ui_s.rotLineEdit.textChanged.connect(self.showGrid)
        self.ui_s.alphaLineEdit.setText(str(int(self.ui_s.sensorImage.gridParam.alpha*100)))
        self.ui_s.alphaLineEdit.textChanged.connect(self.showGrid)

        # Line edit returnPressed
        # self.ui_s.IPComboBox.change　.connect(self.changeIPaddress)
        self.ui_s.hex4dLineEdit.returnPressed.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        # Push buttons
        self.ui_s.connectButton.clicked.connect(self.connectToSensor)
        self.ui_s.disconnectButton.clicked.connect(self.disconnectSensor)
        self.ui_s.searchButton.clicked.connect(self.searchSensor)
        self.ui_s.smidDicEditBtn.clicked.connect(self.editsmiddic)
        # self.ui_s.setIPaddressButton.clicked.connect(self.changeIPaddress)
        self.ui_s.evenLaserButton.clicked.connect(lambda: self.setLaser('0xAAAA'))
        self.ui_s.oddLaserButton.clicked.connect(lambda: self.setLaser('0x5555'))
        self.ui_s.onAllLaserButton.clicked.connect(lambda: self.setLaser('0xFFFF'))
        self.ui_s.offAllLaserButton.clicked.connect(lambda: self.setLaser('0x0000'))
        self.ui_s.setHex4dLaserButton.clicked.connect\
            (lambda: self.setLaser('0x' + self.ui_s.hex4dLineEdit.text()))

        self.ui_s.consecutiveModeButton.clicked.connect(lambda: self.startGetImageThread(1, False))
        self.ui_s.prev1Button.clicked.connect(lambda: self.startGetImageThread(1, False))
        self.ui_s.prevAveButton.clicked.connect(lambda: self.startGetImageThread(self.frames, False))
        self.ui_s.save1Button.clicked.connect(lambda: self.startGetImageThread(1, True))
        self.ui_s.saveAveButton.clicked.connect(lambda: self.startGetImageThread(self.frames, True))
        self.ui_s.frameButton.clicked.connect(self.snap3D)

        self.ui_s.selectDirectoryButton.clicked.connect(self.selectDirectory)
        self.ui_s.resetButton.clicked.connect(self.resetCounter)
        # self.ui_s.gridButton.clicked.connect(self.showGrid)
        self.ui_s.gridGroup.clicked.connect(self.showGrid)

        # Label
        # self.ui_s.CurrentLaserPattern_value.setText(str(format(0, '016b')))
        # self.ui_s.CurrentLaserPattern_value.setText('-'.join(self.binLaserPattern.replace('0b', '').zfill(16)))
        self.ui_s.CurrentLaserPattern_value.setText('0000-0000-0000-0000')
        self.ui_s.saveDirecoryName.setText(self.captureDirPath)
        self.ui_s.saveImgName.setText('img_' + str(self.imgCounter).zfill(4) + '.png')

        # image
        self.img: QtGui.QPixmap() = None
        self.imgPath = ''
        self.saveImgBool = False

        # 3D frame data
        self.frame3DDirPath = os.getcwd() + '/frame3Ddata'

        # group
        self.ui_s.cameraControlGroup.setEnabled(False)
        self.ui_s.laserControlGroup.setEnabled(False)


    def changeIPaddress(self):
        self.RPiaddress = self.ui_s.IPComboBox.currentText()
        if ':' in self.RPiaddress:
            # https://teratail.com/questions/61914
            pattern = "(.*):(.*)"
            d = re.search(pattern, self.RPiaddress)
            self.IPaddress = d.group(1)
            self.portNum = int(d.group(2))
        else:
            self.IPaddress = self.RPiaddress


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
            print(self.getImg_thread)
            if self.getImg_thread is not None:
                if self.getImg_thread.alive:
                    self.getImg_thread.change_frame(self.frames)

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

        try:
            self.changeIPaddress()
            self.sensor = SensorDevice.SensorDevice()
            self.sensor.open(self.IPaddress, self.portNum)
            i = self.ui_s.IPComboBox.findText(self.RPiaddress, Qt.MatchExactly)
            while i >= 0:
                self.ui_s.IPComboBox.removeItem(i)
                i = self.ui_s.IPComboBox.findText(self.RPiaddress, Qt.MatchExactly)
            self.ui_s.IPComboBox.insertItem(0, self.RPiaddress)
            self.ui_s.IPComboBox.setCurrentIndex(0)

            # initialize values
            self.changeShutter()
            self.changeFrames()
            self.changeISO()
            self.setLaser('0x0000')

            self.ui_s.cameraStatusLabel.setText('Successfully connected to sensor and set parameter values')
            # get smid
            stats = self.sensor.get_stats()
            print(stats)
            smid = stats.get("runtime_info", {}).get("sensor_discovery", {}).get("configured", {}).get("smid") if type(stats) == dict else None
            print(smid)
            self.ui_s.textSerial.setText(smid)

            self.sensorInfo.clear()
            self.sensorInfo.smid = smid
            self.sensorInfo.labelid_from_smid()

            lblid = self.sensorInfo.labelid
            self.ui_s.textLabelID.setText(lblid)
            if lblid != None and len(lblid) > 0:
                self.ui_s.textLabelID.setStyleSheet("QLineEdit { background: rgb(255, 255, 255);}")
            else:
                self.ui_s.textLabelID.setStyleSheet("QLineEdit { background: rgb(255, 255, 0);}")


            # どうにかする
            # self.ui_s.setIPaddressButton.setEnabled(False)
            self.ui_s.connectButton.setEnabled(False)
            self.ui_s.IPComboBox.setEnabled(False)
            self.ui_s.disconnectButton.setEnabled(True)
            self.ui_s.searchButton.setEnabled(False)
            self.ui_s.cameraControlGroup.setEnabled(True)
            self.ui_s.laserControlGroup.setEnabled(True)
            # self.ui_s.gridButton.setEnabled(True)
            self.ui_s.gridGroup.setEnabled(True)

            self.conn = True
            # print(self.sensor)
            self.getImg_thread = GetImageThread(self.sensor, self.getImgCallback)



        except Exception as e:
            self.ui_s.cameraStatusLabel.setText('!!! Sensor was not detected.')
            QtWidgets.QMessageBox.warning(self, "Connection Failed", str(e))
            print(e)
            # self.ui_s.setIPaddressButton.setEnabled(True)
            self.ui_s.connectButton.setEnabled(True)
            self.ui_s.IPComboBox.setEnabled(True)
            self.ui_s.disconnectButton.setEnabled(False)
            self.ui_s.searchButton.setEnabled(True)
            self.ui_s.cameraControlGroup.setEnabled(False)
            self.ui_s.laserControlGroup.setEnabled(False)

            # self.ui_s.sensorImage.setScene(self.scene)

            self.conn = False

        except TimeoutError:
            QtWidgets.QMessageBox.critical(self, "Connection Error", "Cannot connect to sensor (timeout)")


        self.mainUI.sensorChanged(self.conn)

    def disconnectSensor(self):
        try:
            self.sensor.close()
            self.ui_s.cameraStatusLabel.setText('The sensor was disconnected.')
            self.conn = False
        except Exception as e:
            self.ui_s.cameraStatusLabel.setText('Could not disconnect the sensor correctly.')
        finally:
            self.ui_s.connectButton.setEnabled(True)
            self.ui_s.IPComboBox.setEnabled(True)
            self.ui_s.disconnectButton.setEnabled(False)
            self.ui_s.searchButton.setEnabled(True)
            self.ui_s.cameraControlGroup.setEnabled(False)
            self.ui_s.laserControlGroup.setEnabled(False)

    def searchSensor(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        list = discoverdevices.discover_devices()
        QApplication.restoreOverrideCursor()
        print(list)

        sensorListWindow = PopupList.PopupList()
        pos = self.ui_s.searchButton.mapToGlobal(QPoint(32, 24))
        width = 240
        height = 200
        rect = QRect(pos.x() - width, pos.y(), width, height)
        sensorListWindow.setGeometry(rect)
        strlist = [list[key] + ":" + key for key in list]
        sensorListWindow.setDic(list)
        sensorListWindow.selected.connect(self.sensorListSelected)
        sensorListWindow.show()

    def sensorListSelected(self, name, adr):
        print(name, adr)
        self.ui_s.IPComboBox.setCurrentText(adr)

    def editsmiddic(self):
        DicFile = "smid_dictionary.csv"
        subprocess.Popen(['xdg-open ' + DicFile], shell=True)

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


    def startGetImageThread(self, frames, saveImgBool):
        self.frames = frames
        self.saveImgBool = saveImgBool

        if self.getImg_thread.ended:
            self.getImg_thread.begin(frames)

    def getImgCallback(self, pixmap, image):
        if pixmap != None:
            self.ui_s.sensorImage.setPixMap(pixmap)
            self.ui_s.sensorImage.show()
            app.processEvents()

            if self.ui_s.consecutiveModeButton.isChecked() and self.ui_s.consecutiveModeButton.isEnabled():
                if self.frames == 1:
                    self.ui_s.prev1Button.click()
                else:
                    self.ui_s.prevAveButton.click()
            else:
                self.getImg_thread.end()

                if self.saveImgBool:
                    self.saveImg(image)


    def prevImg(self, frames):
        image, pixmap = self.getImg(frames)
        self.ui_s.sensorImage.setPixMap(pixmap)
        self.ui_s.sensorImage.show()

    def saveImg(self, image):
        if self.captureDirPath == '':
            QtWidgets.QMessageBox.critical(self, "Folder not found",
                                           "Please specify a folder where captured imaged to be saved.")
        else:
            saveName = self.captureDirPath + '/img_' + str(self.imgCounter).zfill(4) + '.png'

            if os.path.exists(saveName):
                ans = QtWidgets.QMessageBox.question(self,'The file already exists',
                                                     "Are you sure to overwrite \n" + saveName + " ?",
                                                     QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                                     defaultButton=QtWidgets.QMessageBox.Yes)
                if ans == QtWidgets.QMessageBox.Yes:
                    image.save(saveName)
                    self.imgCounter += 1
                else:
                    pass
            else:
                image.save(saveName)
                self.imgCounter += 1
            self.ui_s.saveImgName.setText('img_' + str(self.imgCounter).zfill(4) + '.png')



    def selectDirectory(self):
        foldername = QtWidgets.QFileDialog.getExistingDirectory(self)
        if foldername == '':  # when cancel pressed
            if self.captureDirPath == '':
                self.captureDirPath = foldername
                self.ui_s.saveDirecoryName.setText(self.captureDirPath)
            else:
                pass
        else:
            self.captureDirPath = foldername
            self.ui_s.saveDirecoryName.setText(self.captureDirPath)


    def getImg(self, frames):
        print('getImg', frames)
        img = self.sensor.get_image(frames)
        # print(img)
        img.format = "PNG"
        img2 = img.get_image()
        image = QtGui.QImage(img2, len(img2[0]), len(img2), QtGui.QImage.Format_Grayscale8)
        pixmap = QtGui.QPixmap(image)
        # img3 = Image.new('L', (len(img2[0]), len(img2)))
        # img3.show()
        return image, pixmap

    def resetCounter(self):
        self.imgCounter = 0
        self.ui_s.saveImgName.setText('img_' + str(self.imgCounter).zfill(4) + '.png')

    def snap3D(self):
        now = datetime.datetime.now()
        ymd_hms = now.strftime('%Y%m%d_%H%M%S')

        frame = self.sensor.get_frame()

        uid = np.array(frame.uid).reshape(-1, 1)
        lut3d = np.array(frame.lut3d)

        data = np.hstack((uid, lut3d))

        if not os.path.exists(self.frame3DDirPath):
            os.makedirs(self.frame3DDirPath)

        f = open(self.frame3DDirPath + '/' + ymd_hms + '.csv', 'w')
        writer = csv.writer(f)
        writer.writerow(['uid', 'x', 'y', 'z'])
        writer.writerows(data)
        f.close()

    def showGrid(self):
        print('--- show grid ---')

        if not self.ui_s.sensorImage.isPixmapSet:
            QtWidgets.QMessageBox.critical(self, "No image",
                                           "There is no image in the Image Viewer. \nPlease capture first.")
            self.ui_s.gridGroup.setChecked(False)
            pass

        self.ui_s.sensorImage.m_gridItem.resetTransform()
        #-- set parameters
        gp = self.ui_s.sensorImage.gridParam
        gp.gridType = self.ui_s.gridTypeCombo.currentText()
        gp.lines_x = int(self.ui_s.xLineEdit.text()) if self.ui_s.xLineEdit.text() != '' else 0
        gp.lines_y = int(self.ui_s.yLineEdit.text()) if self.ui_s.yLineEdit.text() != '' else 0
        gp.rot = float(self.ui_s.rotLineEdit.text()) if self.ui_s.rotLineEdit.text() != '' else 0.0
        gp.color = self.ui_s.gridColorCombo.currentText()
        gp.alpha = float(self.ui_s.alphaLineEdit.text())/100 if self.ui_s.alphaLineEdit.text() != '' else 0.0
        gp.qcolor = QtGui.QColor(*gp.colorDict[gp.color])
        gp.qcolor.setAlphaF(gp.alpha)
        gp.offset_x = float(self.ui_s.xOffsetLineEdit.text()) if self.ui_s.xOffsetLineEdit.text() != '' else 0.0
        gp.offset_y = float(self.ui_s.yOffsetLineEdit.text()) if self.ui_s.yOffsetLineEdit.text() != '' else 0.0
        gp.pen = QtGui.QPen(gp.qcolor)
        gp.pen.setStyle(gp.pen_styles[gp.gridType])

        self.ui_s.sensorImage.setGridParameter(self.ui_s.sensorImage.gridParam)
        self.ui_s.sensorImage.setGridVisible(self.ui_s.gridGroup.isChecked())


    def smidDictionary(self):
        DicFile = "smid_dictionary.csv"
        if type(self.smidDic) != dict or len(self.smidDic) == 0:
            # read smid dictionary
            self.smidDic = {}
            with open(DicFile, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self.smidDic[row['smid']] = row['lblid']
        print(self.smidDic)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sensorWindow = SensorWindow()
    sensorWindow.show()
    app.exec_()
