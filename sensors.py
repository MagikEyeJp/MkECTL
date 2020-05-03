from PyQt5 import QtWidgets, QtGui, QtCore

import sensorwindow_ui


class SensorWindow(QtWidgets.QWidget):   # 20200325remote https://teratail.com/questions/118024
    def __init__(self, parent=None):
        super(SensorWindow, self).__init__(parent)

        self.ui_s = sensorwindow_ui.Ui_sensor()
        self.ui_s.setupUi(self)
