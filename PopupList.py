from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class PopupList(QDialog):
    # select signal
    selected = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowFlags(Qt.Popup)
        listWidget = QListWidget()
        self.tableWidget = QTableWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.tableWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def setDic(self, dic):
        self.dic = dic
        self.tableWidget.clear()
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setRowCount(len(dic))
        self.tableWidget.setHorizontalHeaderLabels(["adr", "name"])
        r = 0
        for item in dic:
            self.tableWidget.setItem(r, 0, QTableWidgetItem(dic[item]))
            self.tableWidget.setItem(r, 1, QTableWidgetItem(item))
            r += 1
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.cellClicked.connect(self.cellClicked)

    def setDic_detailedSettings(self):
        self.dic_settings = \
            {'P (speed)': [0.2, 0.2, 0.2],
             'I (speed)': [0.2, 0.2, 0.2],
             'D (speed)': [0.2, 0.2, 0.2],
             'P (position)': [0.2, 0.2, 0.2],
             'I (position)': [0.2, 0.2, 0.2],
             'D (position)': [0.2, 0.2, 0.2],
             'P (Current)': [0.2, 0.2, 0.2],
             'I (Current)': [0.2, 0.2, 0.2],
             'D (Current)': [0.2, 0.2, 0.2]
             }

        self.tableWidget.clear()
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setRowCount(len(self.dic_settings))
        self.tableWidget.setHorizontalHeaderLabels(["param", "slider", "pan", "tilt"])
        r = 0
        for name, value in self.dic_settings.items():
            self.tableWidget.setItem(r, 0, QTableWidgetItem(name))
            self.tableWidget.setItem(r, 1, QTableWidgetItem(str(value[0])))
            self.tableWidget.setItem(r, 2, QTableWidgetItem(str(value[1])))
            self.tableWidget.setItem(r, 3, QTableWidgetItem(str(value[2])))
            r += 1
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.cellClicked.connect(self.changeDetailedSettengs)

    def show(self):
        self.exec_()


    def cellClicked(self, row, col):
        self.selected.emit(list(self.dic.keys())[row], list(self.dic.values())[row])
        self.close()

    def changeDetailedSettengs(self, row):
        # ここで本当はpidパラメータを変更するor main windowに返す？
        self.selected.emit(list(self.dic_settings.keys())[row], list(self.dic_settings.values())[row])

