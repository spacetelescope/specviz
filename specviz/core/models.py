import uuid

import astropy.units as u
import numpy as np
import qtawesome as qta
from qtpy.QtCore import (QCoreApplication, QModelIndex, QSortFilterProxyModel,
                         Qt, QVariant, Slot)
from qtpy.QtGui import QColor, QIcon, QPixmap, QStandardItemModel

from specutils import Spectrum1D

from .items import DataItem, PlotDataItem


class DataListModel(QStandardItemModel):
    """
    Base model for all data loaded into specviz.
    """
    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

    def add_data(self, spec, name):
        """
        """
        data_item = DataItem(name, identifier=uuid.uuid4(), data=spec)
        self.appendRow(data_item)

    # def flags(self, index):
    #     """Qt interaction flags for each `ListView` item."""
    #     flags = super(DataListModel, self).flags(index)
    #     flags = Qt.ItemFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable |
    #                          Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)

    #     return flags

    def data(self, index, role=Qt.DisplayRole):
        """
        Returns information about an item in the model depending on the
        provided role.
        """
        if not index.isValid():
            return

        item = self.itemFromIndex(index)

        if role == Qt.DisplayRole:
            return item.data(item.NameRole)
        elif role == item.DataRole:
            return item.data(item.DataRole)
        elif role == Qt.UserRole:
            return item

        return super(DataListModel, self).data(index, role)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        item = self.itemFromIndex(index)

        if role == Qt.EditRole:
            if value != "":
                item.setData(value, role=Qt.UserRole + 1)

        return super(DataListModel, self).setData(index, value, role)


class PlotProxyModel(QSortFilterProxyModel):
    def __init__(self, source=None, *args, **kwargs):
        super(PlotProxyModel, self).__init__(*args, **kwargs)

        self.setSourceModel(source)

        self._items = {}

    def item_from_index(self, index):
        index = self.mapToSource(index)
        data_item = self.sourceModel().data(index, role=Qt.UserRole)

        if data_item.identifier not in self._items:
            self._items[data_item.identifier] = PlotDataItem(data_item)

        item = self._items.get(data_item.identifier)

        return item

    def data(self, index, role=Qt.DisplayRole):
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
        elif role == Qt.CheckStateRole:
            item.data_item.setCheckState(Qt.Checked if item.visible else ~Qt.Checked)

        return super(PlotProxyModel, self).data(index, role)

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return

        item = self.item_from_index(index)

        if role == Qt.CheckStateRole:
            item.visible = value > 0

            value = Qt.Checked if item.visible else ~Qt.Checked
            item.data_item.setCheckState(value)

        return super(PlotProxyModel, self).setData(index, value, role)
