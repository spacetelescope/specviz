import numpy as np
from qtpy.QtCore import QObject, Property, Signal, Slot

from astropy.units import spectral, spectral_density


class DataItem(QObject):
    name_changed = Signal(str)
    data_unit_changed = Signal(str)
    spectral_axis_unit_changed = Signal(str)
    color_changed = Signal(str)
    visibility_changed = Signal(bool)

    def __init__(self, name, identifier, data, unit=None,
                 spectral_axis_unit=None, color=None, visible=True, *args,
                 **kwargs):
        super(DataItem, self).__init__(*args, **kwargs)

        self._name = name
        self._identifier = identifier
        self._data = data
        self._data_unit = unit or self._data.unit.to_string()
        self._spectral_axis_unit = (spectral_axis_unit or
                                    self._data.wcs.spectral_axis_unit.to_string())
        self._color = color or '#000000'
        self._visible = visible

        # Set the attributes of this plot data item
        

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
        return self._data.flux.to(self.data_unit,
                                  equivalencies=spectral_density(
                                      self.spectral_axis)).value

    @Property(list)
    def spectral_axis(self):
        return self._data.spectral_axis.to(self.spectral_axis_unit,
                                           equivalencies=spectral()).value

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
