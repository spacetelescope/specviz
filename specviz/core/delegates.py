from qtpy.QtCore import Qt
from qtpy.QtWidgets import QStyledItemDelegate


class DataItemDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(DataItemDelegate, self).__init__(*args, **kwargs)

    def flags(self, index):
        flags = super(DataItemDelegate, self).flags(index)
        flags = Qt.ItemIsEditable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

        return flags

    # def paint(self, painter, option, index):
    #     item_var = index.data(Qt.DisplayRole)
    #     item_str = item_var.toPyObject()
    #
    #     opts = QStyleOptionProgressV2()
    #     opts.rect = option.rect