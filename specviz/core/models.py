import uuid

import numpy as np
import qtawesome as qta
from qtpy.QtCore import (QModelIndex, Qt, QVariant, Slot,
                         QCoreApplication, QSortFilterProxyModel)
from qtpy.QtGui import QColor, QIcon, QPixmap, QStandardItemModel

from specutils import Spectrum1D
import astropy.units as u

from .items import DataItem, PlotDataItem


class DataListModel(QStandardItemModel):
    """
    Base model for all data loaded into specviz.
    """
    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

        spec1 = Spectrum1D(flux=np.random.sample(100) * u.Jy,
                           spectral_axis=np.arange(100) * u.AA)

        data_item = DataItem("My Data 1", identifier=uuid.uuid4(), data=spec1)

        self.appendRow(data_item)

        self.setup_connections()

    def setup_connections(self):
        pass

    # def flags(self, index):
    #     """Qt interaction flags for each `ListView` item."""
    #     flags = super(DataListModel, self).flags(index)
    #     flags |= Qt.ItemIsUserCheckable

    #     return flags

    # def rowCount(self, parent=QModelIndex(), **kwargs):
    #     """Returns the number of items in the model."""
    #     return len(self._items)

    def data(self, index, role=None, *args, **kwargs):
        """
        Returns information about an item in the model depending on the
        provided role.
        """
        if not index.isValid():
            return

        item = self.itemFromIndex(index)

        if role == Qt.DisplayRole:
            return item.data(Qt.UserRole + 1)
        elif role == Qt.DecorationRole:
            icon = qta.icon('fa.ellipsis-v',
                            color='black',)
            return icon
        elif role == Qt.UserRole + 3:
            return item.data(Qt.UserRole + 3)

        return super(DataListModel, self).data(index, role, *args, **kwargs)

    def setData(self, index, value, role=Qt.EditRole, *args, **kwargs):
        if not index.isValid():
            return False

        item = self.itemFromIndex(index)

        if role == Qt.EditRole:
            if value != "":
                item.setData(value, role=Qt.UserRole + 1)

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
