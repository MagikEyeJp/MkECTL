# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/magikeye/bin/keiganGUI/oldCodes/sw2/sw2.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_sw2(object):
    def setupUi(self, sw2):
        sw2.setObjectName("sw2")
        sw2.resize(400, 300)
        self.sensorImage = QtWidgets.QGraphicsView(sw2)
        self.sensorImage.setGeometry(QtCore.QRect(40, 10, 311, 271))
        self.sensorImage.setObjectName("sensorImage")

        self.retranslateUi(sw2)
        QtCore.QMetaObject.connectSlotsByName(sw2)

    def retranslateUi(self, sw2):
        _translate = QtCore.QCoreApplication.translate
        sw2.setWindowTitle(_translate("sw2", "Sensor Window"))
