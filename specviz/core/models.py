import numpy as np
import qtawesome as qta
from qtpy.QtCore import QAbstractListModel, QModelIndex, Qt, QVariant, Slot
from qtpy.QtGui import QColor, QIcon, QPixmap

from .items import DataItem


class DataListModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

        self._items = [
            DataItem(identifier="1", name="My data {}".format(np.random.randint(0, 100)), color="cyan", parent=self),
            DataItem(identifier="2", name="My data {}".format(np.random.randint(0, 100)), color="blue", visible=False, parent=self),
            DataItem(identifier="3", name="My data {}".format(np.random.randint(0, 100)), color="red", parent=self),
            DataItem(identifier="4", name="My data {}".format(np.random.randint(0, 100)), color="green", parent=self),
        ]

        # The data model needs to listen for add data events
        # self._hub = Hub()
        # self._hub.subscribe(AddDataMessage, self.add_data, self)
        # self._hub.subscribe(AddPlotDataMessage, self.add_data, self)

    def flags(self, index):
        flags = super(DataListModel, self).flags(index)
        flags |= Qt.ItemIsEditable | Qt.ItemIsEnabled

        return flags

    def rowCount(self, parent=QModelIndex(), **kwargs):
        return len(self._items)

    def data(self, index, role=None):
        if not index.isValid():
            return

        item = self._items[index.row()]

        if role == Qt.DisplayRole:
            return item.name
        elif role == Qt.DecorationRole:
            icon = qta.icon('fa.eye' if item.visible else 'fa.eye-slash',
                            color=item.color)
            return icon

        return QVariant()

    def insertRow(self, row, parent=QModelIndex(), **kwargs):
        self.beginInsertRows(parent, row, row + 1)
        self._items.insert(row, DataItem(name="New data item", color="black"))
        self.endInsertRows()

    def insertRows(self, row, count, parent=QModelIndex(), **kwargs):
        self.beginInsertRows(parent, row, row + count - 1)
        for i in count:
            self._items.insert(row + i, DataItem(name="New data item", color="black"))
        self.endInsertRows()

    @Slot(int)
    def removeRow(self, p_int, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, p_int, p_int)
        self._items.pop(p_int)
        self.endRemoveRows()

        return True

    def removeRows(self, p_int, p_int_1, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, p_int, p_int_1)
        del self._items[p_int:p_int_1 + 1]
        self.endRemoveRows()

        return True

    def setData(self, index, value, *args, **kwargs):
        if not index.isValid():
            return False

        if not 0 <= index.row() < self.rowCount():
            self._items.append(value)
        else:
            self._items[index.row()] = value

        return True
