import numpy as np
import pyqtgraph as pg
from qtpy.QtCore import Property, QObject, Signal, Slot

from astropy.units import spectral, spectral_density


class DataItem(QObject):
    name_changed = Signal(str)

    def __init__(self, name, identifier, data, unit=None,
                 spectral_axis_unit=None, color=None, visible=True, *args,
                 **kwargs):
        super(DataItem, self).__init__(*args, **kwargs)

        self._name = name
        self._identifier = identifier
        self._data = data

    @property
    def identifier(self):
        return self._identifier

    @Property(str, notify=name_changed)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.name_changed.emit(self._name)

    @Property(list)
    def flux(self):
        return self._data.flux

    @Property(list)
    def spectral_axis(self):
        return self._data.spectral_axis


class PlotDataItem(pg.PlotDataItem):
    data_unit_changed = Signal(str)
    spectral_axis_unit_changed = Signal(str)
    color_changed = Signal(str)
    visibility_changed = Signal(bool)

    def __init__(self, data_item, *args, **kwargs):
        super(PlotDataItem, self).__init__(*args, **kwargs)

        self._data_item = data_item
        self._data_unit = self._data_item.flux.unit.to_string()
        self._spectral_axis_unit = self._data_item.spectral_axis.unit.to_string()
        self._color = '#000000'
        self._visible = False

        # Set data
        self.set_data()
        self.setPen(color=self.color)

        if not self.visible:
            self.setPen(None)

        # Connect slots to data item signals
        self.data_unit_changed.connect(self.set_data)
        self.spectral_axis_unit_changed.connect(self.set_data)

        # Connect to color signals
        self.color_changed.connect(lambda c: self.setPen(color=c) if self.visible else None)
        self.visibility_changed.connect(lambda s: self.setPen(None) if not s else self.setPen(self.color))

    @Property(str, notify=data_unit_changed)
    def data_unit(self):
        return self._data_unit

    @data_unit.setter
    def data_unit(self, value):
        self._data_unit = value
        self.data_unit_changed.emit(self._data_unit)

    @Property(str, notify=spectral_axis_unit_changed)
    def spectral_axis_unit(self):
        return self._spectral_axis_unit

    @spectral_axis_unit.setter
    def spectral_axis_unit(self, value):
        self._spectral_axis_unit = value
        self.spectral_axis_unit_changed.emit(self._spectral_axis_unit)

    @Property(list)
    def flux(self):
        return self._data_item.flux.to(self.data_unit,
                                       equivalencies=spectral_density(
                                           self.spectral_axis)).value

    @property
    def spectral_axis(self):
        return self._data_item.spectral_axis.to(self.spectral_axis_unit,
                                                equivalencies=spectral()).value

    @Property(str, notify=color_changed)
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.color_changed.emit(self._color)

    @Property(bool, notify=visibility_changed)
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        self.visibility_changed.emit(self._visible)

    def update_data(self):
        # Replot data
        self.setData(self.spectral_axis, self.flux)

    def set_data(self):
        self.setData(self.spectral_axis, self.flux)
