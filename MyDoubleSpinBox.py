from PySide6 import QtWidgets, QtGui, QtCore


class MyDoubleSpinBox(QtWidgets.QDoubleSpinBox):

    valueDetermined = QtCore.Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.emittable = True
        self.fix()

    def allowDetermine(self, enable):
        self.emittable = enable

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            # self.editingFinished()
            super().keyPressEvent(event)
            self.determine()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.undo()
        else:
            super().keyPressEvent(event)
            self.updateColor()

    def updateColor(self):
        if self.value() == self.undoText:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("QDoubleSpinBox { color:red }")

    def stepBy(self, steps: int) -> None:
        # self.undo()
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ShiftModifier:
            steps *= 10
        super().stepBy(steps)
        self.determine()

    def determine(self):
        if self.emittable:
            self.fix()
            self.valueDetermined.emit()

    def setValue(self, val: float) -> None:
        super().setValue(val)
        self.fix()

    def isModified(self):
        return self.undoText != self.value()

    def fix(self):
        self.undoText = self.value()
        self.updateColor()

    def undo(self):
        self.setValue(self.undoText)
        self.updateColor()
