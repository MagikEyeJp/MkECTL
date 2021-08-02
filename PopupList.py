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

    def setDic_detailedSettings(self, robot):
        # self.dic_settings = \
        #     {'P (speed)': [0.2, 0.2, 0.2],
        #      'I (speed)': [0.2, 0.2, 0.2],
        #      'D (speed)': [0.2, 0.2, 0.2],
        #      'P (position)': [0.2, 0.2, 0.2],
        #      'I (position)': [0.2, 0.2, 0.2],
        #      'D (position)': [0.2, 0.2, 0.2],
        #      'P (current)': [0.2, 0.2, 0.2],
        #      'I (current)': [0.2, 0.2, 0.2],
        #      'D (current)': [0.2, 0.2, 0.2]
        #      }

        self.tableWidget.clear()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(len(robot.pid_settings)*3)
        self.tableWidget.setHorizontalHeaderLabels(["", "param", "slider", "pan", "tilt"])
        r = 0
        col = 2

        for i in range(len(robot.params.keys())):
            for pid_category in ['speed', 'position', 'qCurrent']:
                for pid_param in ['P', 'I', 'D']:
                    # execCode = 'p[\'cont\'].read_%s%s()' % (pid_category, pid_param)
                    # val = eval(execCode)
                    val = robot.pid_settings[pid_category][pid_param][i]

                    self.tableWidget.setItem(r, 1, QTableWidgetItem(pid_param))
                    self.tableWidget.setItem(r, col, QTableWidgetItem(str(val)))
                    r += 1
            r = 0
            col += 1


        self.tableWidget.setSpan(0, 0, 3, 1)    # speed
        self.tableWidget.setSpan(3, 0, 3, 1)    # position
        self.tableWidget.setSpan(6, 0, 3, 1)    # current
        self.tableWidget.setItem(0, 0, QTableWidgetItem("speed"))
        self.tableWidget.setItem(3, 0, QTableWidgetItem("position"))
        self.tableWidget.setItem(6, 0, QTableWidgetItem("current"))

        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        # QTableView.setSpan(row, column, rowSpan, columnSpan)

        self.tableWidget.cellChanged.connect(self.changeDetailedSettings)

    def show(self):
        self.exec_()


    def cellClicked(self, row, col):
        self.selected.emit(list(self.dic.keys())[row], list(self.dic.values())[row])
        self.close()

    def changeDetailedSettings(self, row, col):
        # ここで本当はpidパラメータを変更するor main windowに返す？
        # row -> 0,1,2:speed 3,4,5:position 6,7,8:qCurrent
        #        0,3,6:P     1,4,7:I        2,5,8:D
        # col -> 2:slider(0) 3:pan(1) 4:tilt(2)
        pid_category_dic = {
            0: 'speed', 1: 'speed', 2: 'speed',
            3: 'position', 4: 'position', 5: 'position',
            6: 'qCurrent', 7: 'qCurrent', 8: 'qCurrent'
        }
        pid_param_dic = {
            0: 'P', 3: 'P', 6: 'P',
            1: 'I', 4: 'I', 7: 'I',
            2: 'P', 5: 'P', 8: 'P'
        }
        print(row, col)
        value = float(self.tableWidget.item(row, col).text())
        print(value)
        self.pidChanged.emit(pid_category_dic[row], pid_param_dic[row], col-2, value)

        # self.close()
