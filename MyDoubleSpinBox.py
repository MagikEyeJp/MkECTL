from PyQt5 import QtWidgets, QtGui, QtCore


class MyDoubleSpinBox(QtWidgets.QDoubleSpinBox):

    returnPressed = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(QtWidgets.QDoubleSpinBox, self).__init__(parent)
        self.undoText = self.value()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # self.editingFinished()
            super(QtWidgets.QDoubleSpinBox, self).keyPressEvent(event)
            self.undoText = self.value()
            self.returnPressed.emit()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.setValue(self.undoText)
        else:
            super(QtWidgets.QDoubleSpinBox, self).keyPressEvent(event)
