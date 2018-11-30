import uuid

import qtawesome as qta
from qtpy.QtCore import QSortFilterProxyModel, Qt, Signal
from qtpy.QtGui import QStandardItemModel

from .items import DataItem, PlotDataItem


class DataListModel(QStandardItemModel):
    """
    Base model for all data loaded into specviz.
    """
    data_added = Signal(DataItem)

    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

    @property
    def items(self):
        """
        Retrieves all the :class:`~specviz.core.items.DataItem`s in this model.
        """
        return [self.item(idx) for idx in range(self.rowCount())]

    def add_data(self, spec, name):
        """
        Generate and add a :class:`~specviz.core.items.DataItem` object to the
        internal Qt data model.

        Parameters
        ----------
        spec : :class:`~specutils.Spectrum1D`
            The spectrum object containing data about the spectrum.
        name : str
            Display string of this data item.
        """
        data_item = DataItem(name, identifier=uuid.uuid4(), data=spec)
        self.appendRow(data_item)

        # Emit custom signal indicating a data item has been added to the model
        self.data_added.emit(data_item)

        return data_item

    def remove_data(self, identifier):
        """
        Removes data given the data item's UUID.

        Parameters
        ----------
        identifier : :class:`~uuid.UUID`
            Assigned id of the :class:`~specviz.core.items.DataItem` object.
        """
        item = self.item_from_id(identifier)

        if item is not None:
            self.removeRow(item.index().row())

    def item_from_id(self, identifier):
        return next((x for x in self.items if x.identifier == identifier))

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

    def clear(self):
        self.beginResetModel()

        for item in self.items:
            self.removeRow(item.index().row())

        self.endResetModel()


class PlotProxyModel(QSortFilterProxyModel):
    def __init__(self, source=None, *args, **kwargs):
        super(PlotProxyModel, self).__init__(*args, **kwargs)

        self.setSourceModel(source)
        self._items = {}

    @property
    def items(self):
        """Returns a list of :class:`PlotDataItems` in the proxy model."""
        return list(self._items.values())

    def item_from_index(self, index):
        index = self.mapToSource(index)
        data_item = self.sourceModel().data(index, role=Qt.UserRole)

        if data_item is None:
            return

        if data_item.identifier not in self._items:
            self._items[data_item.identifier] = PlotDataItem(data_item)

        item = self._items.get(data_item.identifier)

        return item

    def item_from_id(self, identifier):
        data_item = self.sourceModel().item_from_id(identifier)

        if data_item.identifier not in self._items:
            self._items[data_item.identifier] = PlotDataItem(data_item)

        item = self._items.get(data_item.identifier)
        return item

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return

        item = self.item_from_index(index)

        if role == Qt.DisplayRole:
            return item.data_item.name
        elif role == Qt.DecorationRole:
            icon = qta.icon('fa.circle' if item.data_item.isEnabled() else 'fa.circle-o',
                            color=item.color)
            return icon
        elif role == Qt.UserRole:
            return item
        elif role == Qt.CheckStateRole:
            return Qt.Checked if item.visible else ~Qt.Checked

        return super(PlotProxyModel, self).data(index, role)

    def setData(self, index, value, role=Qt.EditRole):

        if not index.isValid():
            return

        item = self.item_from_index(index)

        if role == Qt.CheckStateRole:
            item.visible = value > 0

            self.dataChanged.emit(index, index)
            self.sourceModel().itemChanged.emit(item.data_item)

            return True

        return super(PlotProxyModel, self).setData(index, value, role)