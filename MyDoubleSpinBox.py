from PyQt5 import QtWidgets, QtGui, QtCore


class MyDoubleSpinBox(QtWidgets.QDoubleSpinBox):

    returnPressed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(QtWidgets.QDoubleSpinBox, self).__init__(parent)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # self.editingFinished()
            super(QtWidgets.QDoubleSpinBox, self).keyPressEvent(event)
            self.returnPressed.emit()
        else:
            super(QtWidgets.QDoubleSpinBox, self).keyPressEvent(event)

