import numpy as np
from qtpy.QtCore import QObject, Property, Signal, Slot


class DataItem(QObject):
    name_changed = Signal(str)
    data_changed = Signal(list)
    spectral_axis_changed = Signal(list)
    data_unit_changed = Signal(str)
    spectral_axis_unit_changed = Signal(str)
    color_changed = Signal(str)
    visibility_changed = Signal(bool)

    def __init__(self, name, identifier, data=None,
                 spectral_axis=None, unit=None, spectral_axis_unit=None,
                 color=None, visible=True, *args, **kwargs):
        super(DataItem, self).__init__(*args, **kwargs)

        self._name = name
        self._identifier = identifier
        self._data = data or []
        self._spectral_axis = spectral_axis or []
        self._data_unit = unit or ''
        self._spectral_axis_unit = spectral_axis_unit or ''
        self._color = color or 'black'
        self._visible = visible

    @property
    def identifier(self):
        return self._identifier

    @Property(str, notify=name_changed)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @Property(list, notify=data_changed)
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @Property(list, notify=spectral_axis_changed)
    def spectral_axis(self):
        return self._spectral_axis

    @spectral_axis.setter
    def spectral_axis(self, value):
        self._spectral_axis = value

    @Property(str, notify=data_unit_changed)
    def data_unit(self):
        return self._data_unit

    @data_unit.setter
    def data_unit(self, value):
        self._data_unit = value

    @Property(str, notify=spectral_axis_unit_changed)
    def spectral_axis_unit(self):
        return self._spectral_axis_unit

    @spectral_axis_unit.setter
    def spectral_axis_unit(self, value):
        self._spectral_axis_unit = value

    @Property(str, notify=color_changed)
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value

    @Property(bool, notify=visibility_changed)
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
