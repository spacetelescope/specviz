import uuid

import astropy.units as u
import numpy as np
import qtawesome as qta
from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from specutils import Spectrum1D

from .items import DataItem, PlotDataItem


class DataListModel(QStandardItemModel):
    """
    Base model for all data loaded into specviz.
    """
    def __init__(self, *args, **kwargs):
        super(DataListModel, self).__init__(*args, **kwargs)

        spec1 = Spectrum1D(flux=np.random.sample(100) * u.Jy,
                           spectral_axis=np.arange(100) * u.AA)

        spec2 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                           spectral_axis=np.arange(100) * u.Hz)

        data_item = DataItem("My Data 1", identifier=uuid.uuid4(), data=spec1)
        data_item2 = DataItem("My Data 2", identifier=uuid.uuid4(), data=spec2)
        data_item3 = DataItem("My Data 3", identifier=uuid.uuid4(), data=spec2)

        self.appendRow(data_item)
        self.appendRow(data_item2)
        self.appendRow(data_item3)

    @property
    def items(self):
        """
        Retrieves all the :class:`~specviz.core.items.DataItem`s in this model.
        """
        return [self.item(idx) for idx in range(self.rowCount())]

    def add_data(self, spec, name):
        """
        """
        data_item = DataItem(name, identifier=uuid.uuid4(), data=spec)
        self.appendRow(data_item)

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
            return item._data_item.name
        elif role == Qt.DecorationRole:
            icon = qta.icon('fa.eye' if item.visible else 'fa.eye-slash',
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


class ModelFittingModel(QStandardItemModel):

    def __init__(self, *args):
        super().__init__(*args)
        from astropy.modeling.models import Gaussian1D, Linear1D

        a = Gaussian1D()
        l = Linear1D()

        self.add_model(a)
        self.add_model(l)

    def add_model(self, model):
        oper_item = QStandardItem("Add")

        model_item = QStandardItem(model.__class__.name)
        model_item.setData(model, Qt.UserRole + 1)

        for para_name in model.param_names:
            # Retrieve the parameter object from the model
            parameter = getattr(model, para_name)

            # Store the name value
            param_name = QStandardItem(parameter.name)
            param_name.setData(parameter, Qt.UserRole + 1)
            param_name.setEditable(False)

            # Store the data value of the parameter
            param_value = QStandardItem("{}".format(parameter.value))
            param_value.setData(parameter.value, Qt.UserRole + 1)

            # Store the unit information
            param_unit = QStandardItem("{}".format(parameter.unit))
            param_unit.setData(parameter.unit, Qt.UserRole + 1)

            # Store the fixed state of the unit
            param_fixed = QStandardItem()
            param_fixed.setData(parameter.fixed, Qt.UserRole + 1)
            param_fixed.setCheckable(True)
            param_fixed.setEditable(False)

            model_item.appendRow([param_name, param_value, param_unit, param_fixed])

        self.appendRow([oper_item, model_item])


class ModelFittingProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, p_int, index):
        if index.row() >= 0:
            return False

        return super().filterAcceptsRow(p_int, index)