import uuid

import numpy as np
import qtawesome as qta
from qtpy.QtCore import (QAbstractListModel, QModelIndex, Qt, QVariant, Slot,
                         QCoreApplication, QSortFilterProxyModel)
from qtpy.QtGui import QColor, QIcon, QPixmap

from specutils import Spectrum1D
import astropy.units as u

from .items import DataItem, PlotDataItem


class DataListModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

        spec1 = Spectrum1D(flux=np.random.sample(100) * u.Jy,
                           spectral_axis=np.arange(100) * u.AA)

        self._items = [
            DataItem(name='MyData 1',
                     identifier=uuid.uuid4(),
                     data=spec1,
                     color='#336699')
        ]

        # Cache a reference to the event hub
        # self._hub = QCoreApplication.instance().hub

        self.setup_connections()

    def setup_connections(self):
        pass

    @property
    def items(self):
        return self._items

    def add_data(self, spectrum, name="Unnamed Spectrum"):
        """
        Adds a new spectrum object to the model as a data item.
        """
        data_item = DataItem(name=name,
                             identifier=uuid.uuid4(),
                             data=spectrum)

        self.insertRow(len(self.items), data_item)

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
            icon = qta.icon('fa.eye-slash',
                            color='black')
            return icon
        elif role == Qt.EditRole:
            pass

        return QVariant()

    def insertRow(self, row, data, parent=QModelIndex(), **kwargs):
        self.beginInsertRows(parent, row, row)
        self._items.insert(row, data)
        self.endInsertRows()

    def insertRows(self, row, count, data, parent=QModelIndex(), **kwargs):
        self.beginInsertRows(parent, row, row + count - 1)
        for i in count:
            self._items.insert(row + i, data[i])
        self.endInsertRows()

    @Slot(int)
    def removeRow(self, p_int, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, p_int, p_int)
        self._items.pop(p_int)
        self.endRemoveRows()

        return True

    def removeRows(self, p_int, p_int_1, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, p_int, p_int_1)
        del self._items[p_int:p_int_1]
        self.endRemoveRows()

        return True

    def setData(self, index, value, role=Qt.EditRole, *args, **kwargs):
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            if value != "":
                self._items[index.row()].name = value

        return True


class PlotProxyModel(QSortFilterProxyModel):
    def __init__(self, source=None, *args, **kwargs):
        super(PlotProxyModel, self).__init__(*args, **kwargs)

        self.setSourceModel(source)

        self._items = {}

    def setup_connections(self):
        pass

    def item_from_index(self, index):
        index = self.mapToSource(index)
        data_item = self.sourceModel().items[index.row()]

        self._items.setdefault(data_item, PlotDataItem(data_item))
        item = self._items.get(data_item)

        return item

    def data(self, index, role=None):
        if not index.isValid():
            return

        item = self.item_from_index(index)

        if role == Qt.DisplayRole:
            return item._data_item.name
        elif role == Qt.DecorationRole:
            icon = qta.icon('fa.eye' if item.visible else 'fa.eye-slash',
                            color=item.color)
            return icon
        elif role == Qt.UserRole:
            return item

        return QVariant()
