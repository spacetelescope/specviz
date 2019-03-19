from itertools import cycle

import astropy.units as u
import numpy as np
import pyqtgraph as pg
from astropy.units import spectral, spectral_density
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QStandardItem, QColor

__all__ = ['DataItem', 'PlotDataItem']


flatui = cycle(["#000000", "#9b59b6", "#3498db", "#95a5a6", "#e74c3c",
                "#34495e", "#2ecc71"])


class DataItem(QStandardItem):
    """
    A Qt wrapper class around :class:`~specutils.Spectrum1D`.

    Parameters
    ----------
    name : str
        The name of this data item.
    identifier : :class:`uuid.UUID`
        The UUID of this data item.
    data : :class:`specutils.Spectrum1D`
        The internal spectrum object associated with this data item.

    Attributes
    ----------
    data_changed : ``Signal``
        Fired when the internal stored data is changed.
    """
    NameRole = Qt.UserRole + 1
    IdRole = Qt.UserRole + 2
    DataRole = Qt.UserRole + 3

    def __init__(self, name, identifier, data, *args, **kwargs):
        super(DataItem, self).__init__(*args, **kwargs)

        self.setData(name, self.NameRole)
        self.setData(identifier, self.IdRole)
        self.setData(data, self.DataRole)
        self.setToolTip(name)

        self.setCheckable(True)

    @property
    def identifier(self):
        """
        A unique identifier for the data.
        """
        return self.data(self.IdRole)

    @property
    def name(self):
        """
        A dislay name for the data.
        """
        return self.data(self.NameRole)

    @name.setter
    def name(self, value):
        self.setData(value, self.NameRole)

    @property
    def flux(self):
        """
        The flux values of the stored :class:`~specutils.Spectrum1D` object.
        """
        return self.data(self.DataRole).flux

    @property
    def spectral_axis(self):
        """
        The spectral axis of the stored :class:`~specutils.Spectrum1D` object.
        """
        return self.data(self.DataRole).spectral_axis

    @property
    def uncertainty(self):
        """
        The flux uncertainty values of the stored :class:`~specutils.Spectrum1D`
        object.
        """
        return self.data(self.DataRole).uncertainty

    def set_data(self, data):
        """
        Update the stored :class:`~specutils.Spectrum1D` data values.
        """
        self.setData(data, self.DataRole)
        self.emitDataChanged()

    @property
    def spectrum(self):
        """
        The stored :class:`~specutils.Spectrum1D` object.
        """
        return self.data(self.DataRole)


class PlotDataItem(pg.PlotDataItem):
    """
    A PyQtGraph `~pyqtgraph.PlotDataItem` object that wraps a `DataItem` object
    (which in turn wraps a :class:`~specutils.Spectrum1D` object).

    Notes
    -----
        Currently, the ``PlotDataItem`` class does not take in a reference to
        the data model. This means that it is not listening to ``dataChanged``
        signals raised from the data items within the model. Thus, if the
        data item for this plot data item is changed, users must call the
        ``set_data`` method on this class to re-render the plot.
    """
    data_unit_changed = Signal(str)
    spectral_axis_unit_changed = Signal(str)
    color_changed = Signal(QColor)
    width_changed = Signal(int)
    visibility_changed = Signal(bool)

    def __init__(self, data_item, color=None, *args, **kwargs):
        super(PlotDataItem, self).__init__(stepMode=True, *args, **kwargs)

        self._data_item = data_item
        self._data_unit = self._data_item.flux.unit.to_string()
        self._spectral_axis_unit = self._data_item.spectral_axis.unit.to_string()
        self._color = color or next(flatui)
        self._width = 1
        self._visible = False

        # Include error bar item
        self._error_bar_item = pg.ErrorBarItem(pen=[128, 128, 128, 200])

        # Set data
        self.set_data()
        self._update_pen()

        # Connect slots to data item signals
        self.data_unit_changed.connect(self.set_data)
        self.spectral_axis_unit_changed.connect(self.set_data)

        # Connect to color signals
        self.color_changed.connect(self._update_pen)
        self.width_changed.connect(self._update_pen)
        self.visibility_changed.connect(self._update_pen)

    def _update_pen(self, *args):
        if self.visible:
            self.setPen(color=self.color, width=float(self.width))
        else:
            self.setPen(None)

    @property
    def data_item(self):
        """
        The underlying `DataItem` object.
        """
        return self._data_item

    @property
    def data_unit(self):
        """
        The unit to use for displaying the flux values in the underlying
        :class:`~specutils.Spectrum1D` object.
        """
        return self._data_unit

    @data_unit.setter
    def data_unit(self, value):
        self._data_unit = value
        self.data_unit_changed.emit(self._data_unit)

    @property
    def error_bar_item(self):
        """
        A PyQtGraph `~pyqtgraph.ErrorBarItem` to represent the uncertainties
        in the underlying :class:`~specutils.Spectrum1D` object.
        """
        spectral_axis = self.spectral_axis

        # If step mode is one, offset the error bars by a half delta so that
        # they cross the middle of the bin.
        if self.opts.get('stepMode'):
            diff = np.diff(spectral_axis)
            spectral_axis += np.append(diff, diff[-1]) * 0.5

        self._error_bar_item.setData(x=spectral_axis,
                                     y=self.flux,
                                     height=self.uncertainty)

        return self._error_bar_item

    def are_units_compatible(self, spectral_axis_unit, data_unit):
        """
        Check whether the specified units are compatible with the spectral axis
        and flux units of the underlying :class:`~specutils.Spectrum1D` object.

        Parameters
        ----------
        spectral_axis_unit : `~astropy.units.Unit`
            The spectral axis unit to test
        data_unit : `~astropy.units.Unit`
            The data unit to test

        Returns
        -------
        bool
            Returns `True` if the both the spectral axis and data units are
            compatble with the underlying spectrum units, and `False` otherwise.
        """
        return self.is_data_unit_compatible(data_unit) and \
            self.is_spectral_axis_unit_compatible(spectral_axis_unit)

    def is_data_unit_compatible(self, unit):
        """
        Check whether the specified unit is compatible with the flux units of
        the underlying :class:`~specutils.Spectrum1D` object.

        Parameters
        ----------
        unit : `~astropy.units.Unit`
            The data unit to test

        Returns
        -------
        bool
            Returns `True` if the specified data unit is compatible, `False`
            otherwise.
        """
        return (unit is not None and
                self.data_item.flux.unit.is_equivalent(
                    unit, equivalencies=spectral_density(
                        self.data_item.spectral_axis)))

    def is_spectral_axis_unit_compatible(self, unit):
        """
        Check whether the specified unit is compatible with the spectral axis
        units of the underlying :class:`~specutils.Spectrum1D` object.

        Parameters
        ----------
        unit : `~astropy.units.Unit`
            The spectral axis unit to test

        Returns
        -------
        bool
            Returns `True` if the specified spectral axis unit is compatible,
            `False` otherwise.
        """
        return (unit is not None and
                self.data_item.spectral_axis.unit.is_equivalent(
                    unit, equivalencies=spectral()))

    @property
    def spectral_axis_unit(self):
        """
        The unit to use for displaying the spectral axis in the underlying
        :class:`~specutils.Spectrum1D` object.
        """
        return self._spectral_axis_unit

    @spectral_axis_unit.setter
    def spectral_axis_unit(self, value):
        value = u.Unit(value).to_string()

        self._spectral_axis_unit = value
        self.spectral_axis_unit_changed.emit(self._spectral_axis_unit)

    def reset_units(self):
        """
        Reset the display units for the spectral axis and the data to those of
        the underlying :class:`~specutils.Spectrum1D` object.
        """
        self.data_unit = self.data_item.flux.unit.to_string()
        self.spectral_axis_unit = self.data_item.spectral_axis.unit.to_string()

    @property
    def flux(self):
        """
        Returns the fluxes of the underlying :class:`~specutils.Spectrum1D`
        object converted to the current data display units (given by
        `PlotDataItem.data_unit`).
        """
        return self.data_item.flux.to(self.data_unit,
                                      equivalencies=spectral_density(
                                          self.data_item.spectral_axis)).value

    @property
    def spectral_axis(self):
        """
        Returns the spectral axis of the underlying :class:`~specutils.Spectrum1D`
        object converted to the current specrtal axis display units (given by
        `PlotDataItem.spectral_axis_unit`).
        """
        return self.data_item.spectral_axis.to(self.spectral_axis_unit or "",
                                               equivalencies=spectral()).value

    @property
    def uncertainty(self):
        """
        Returns the uncertainties of the underlying
        :class:`~specutils.Spectrum1D` object converted to the current data
        display units (given by `PlotDataItem.data_unit`).

        If no uncertainties are present, `None` is returned.
        """
        if self.data_item.uncertainty is None:
            return

        uncertainty = self.data_item.uncertainty.array * \
                      self.data_item.uncertainty.unit

        return uncertainty.to(self.data_unit or "",
                              equivalencies=spectral_density(
                                  self.data_item.spectral_axis)).value

    @property
    def color(self):
        """
        The display color to use for the spectrum.
        """
        return self._color

    @color.setter
    def color(self, value):
        self._color = QColor(value).toRgb()
        self.color_changed.emit(self._color)
        self.data_item.emitDataChanged()

    @property
    def width(self):
        """
        The display line width to use for the spectrum.
        """
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self.width_changed.emit(self._width)
        self.data_item.emitDataChanged()

    @property
    def zorder(self):
        """
        A value indicating the order in which plot items should be drawn.

        Larger values indicate items that are drawn later on and therefore will
        appear in front of other plot items.
        """
        return self.zValue()

    @zorder.setter
    def zorder(self, value):
        self.setZValue(value)
        self.data_item.emitDataChanged()

    @property
    def visible(self):
        """
        A boolean value indicating whether the spectrum is currently visible.
        """
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        self.visibility_changed.emit(self._visible)

    def set_data(self):
        """
        Sets the spectral_axis and flux. self.flux is called to convert flux
        units if they had been changed.
        """
        spectral_axis = self.spectral_axis

        if self.opts.get('stepMode'):
            spectral_axis = np.append(self.spectral_axis, self.spectral_axis[-1])

        self.setData(spectral_axis, self.flux, connect="finite")

        # Without this call, the plot tries to do autoRange based on DataItem (which does not change), when it should
        # instead be doing autoRange based on PlotDataItem, which updates based on what units are being used
        self._error_bar_item.setData(x=self.spectral_axis,
                                     y=self.flux,
                                     height=self.uncertainty)

    def getData(self):
        """
        Override getData method to ensure that the returned values fit the
        requirements of the pyqtgraph step mode: len(x) == len(y) + 1.
        Necessary for proper performance implementations.
        """
        try:
            x, y = super().getData()
        except (ValueError, IndexError):
            # if error occurred during down-sampling and clip to view use original data
            x, y = self.xData, self.yData

        # only if we have digital signal
        if self.opts["stepMode"] and (self.opts['clipToView'] or
                                      self.opts['autoDownsample']):

            # if there is data
            if x is not None:
                # if step mode is enabled and len(x) != len(y) + 1
                if len(x) == len(y):
                    if len(x) > 0:
                        x = np.append(x, x[-1])

            if (x is None and y is None) or (len(x) == 0 and len(y) == 0):
                x = np.array([0, 0])
                y = np.array([0])

        return x, y
