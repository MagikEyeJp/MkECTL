from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class PopupList(QDialog):
    # select signal
    selected = pyqtSignal(str, str)
    pidChanged = pyqtSignal(str, str, int, float)

    def __init__(self, parent=None):
        super().__init__()
        self.setWindowFlags(Qt.Popup)
        listWidget = QListWidget()
        self.tableWidget = QTableWidget()
        self.tableWidget2 = QTableWidget()
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

    def show(self):
        self.exec_()

    def cellClicked(self, row, col):
        self.selected.emit(list(self.dic.keys())[row], list(self.dic.values())[row])
        self.close()

