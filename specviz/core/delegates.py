from qtpy.QtCore import Qt
from qtpy.QtWidgets import QStyledItemDelegate, QPushButton


class DataItemDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(DataItemDelegate, self).__init__(*args, **kwargs)

    def flags(self, index):
        flags = super(DataItemDelegate, self).flags(index)
        flags = Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

        return flags

    def createEditor(self, parent, option, index):
        editor = QPushButton("O", parent)

        return editor

    def setEditorData(self, editor, index):
        value = 10
        editor.setValue(value)

    def setModelData(self, edit, model, index):
        pass

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)