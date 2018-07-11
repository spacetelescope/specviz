import os

import numpy as np
import pyqtgraph as pg
import qtawesome as qta
from qtpy.QtCore import Property, QModelIndex, QObject, Qt, Signal
from qtpy.QtWidgets import QAction, QListWidget, QMainWindow, QMdiSubWindow
from qtpy.uic import loadUi

from ..core.models import PlotProxyModel
from ..utils import UI_PATH


class PlotWindow(QMdiSubWindow):
    """
    Displayed plotting subwindow availabel in the `QMdiArea`.
    """
    def __init__(self, model, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)

        # The central widget of the sub window will be a main window so that it
        # can support having tab bars
        self._main_window = QMainWindow()
        self.setWidget(self._main_window)

        loadUi(os.path.join(UI_PATH, "plot_window.ui"), self._main_window)

        # The central widget of the main window widget will be the plot
        self._model = model
        self._plot_widget = PlotWidget(model=self._model)
        self._main_window.setCentralWidget(self._plot_widget)

        # Add the qtawesome icons to the plot-specific actions
        self._main_window.linear_region_action.setIcon(
            qta.icon('fa.compress',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.rectangular_region_action.setIcon(
            qta.icon('fa.square',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.plot_options_action.setIcon(
            qta.icon('fa.line-chart',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.export_plot_action.setIcon(
            qta.icon('fa.download',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

    @property
    def plot_widget(self):
        return self._plot_widget

    @property
    def proxy_model(self):
        return self.plot_widget.proxy_model

    def setup_connections(self):
        pass


class PlotWidget(pg.PlotWidget):
    """
    The Qt widget housing all aspects of a single plot window. This includes
    axes, plot data items, labels, etc.

    Upon initialization of a new plot widget, items from the
    :class:`~specviz.core.models.DataListModel` are added to the plot. The
    first item that is added defines the units for the entire plot. Subsequent
    data items will attempt to have their units converted.

    Parameters
    ----------
    name : str
        The name of this particular plot window.
    model : :class:`~specviz.core.models.DataListModel`
        The core model for this specviz instance. This will be referenced
        through a proxy model when used for plotting.
    visible : bool, optional
        This overrides the individual plot data item visibility on
        initialization of the plot widget.

    Signals
    -------
    plot_added : None
        Fired when a plot data item has been added to the plot widget.
    plot_removed : None
        Fired when a plot data item has been removed from the plot widget.
    """
    plot_added = Signal()
    plot_removed = Signal()

    def __init__(self, name=None, model=None, visible=True, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self._name = name or "Untitled Plot"
        self._plot_item = self.getPlotItem()
        self._visible = visible

        # Define labels for axes
        self._plot_item.setLabel('bottom', text='Wavelength')
        self._plot_item.setLabel('left', text='Flux')

        # Store the unit information for this plot. This is defined by the
        # first data set that gets plotted. All other data sets will attempt
        # to be converted to these units.
        self._data_unit = None
        self._spectral_axis_unit = None

        # Cache a reference to the model object that's attached to the parent
        self._proxy_model = PlotProxyModel(model)

        # Listen for model events to add/remove items from the plot
        # self.proxy_model.rowsInserted.connect(self._check_unit_compatibility)
        self.proxy_model.rowsAboutToBeRemoved.connect(self.remove_plot)
        self.proxy_model.sourceModel().itemChanged.connect(self.on_item_changed)

    @property
    def name(self):
        return self._name

    @property
    def proxy_model(self):
        return self._proxy_model

    @property
    def data_unit(self):
        return self._data_unit

    @property
    def spectral_axis_unit(self):
        return self._spectral_axis_unit

    def on_item_changed(self, item):
        """
        Called when the user clicks the item's checkbox.
        """
        source_index = self.proxy_model.sourceModel().indexFromItem(item)
        proxy_index = self.proxy_model.mapFromSource(source_index)

        if item.checkState() == Qt.Checked:
            self.add_plot(proxy_index,
                          visible=True,
                          initialize=len(self.listDataItems()) == 0)
        else:
            self.remove_plot(proxy_index)

    def _check_unit_compatibility(self, index, first=None, last=None):
        plot_data_item = self.proxy_model.item_from_index(index)

        if self._data_unit is not None and \
            not plot_data_item.is_data_unit_compatible(self._data_unit):
            plot_data_item.setEnabled(False)

    def add_plot(self, index, first=None, last=None, visible=True,
                 initialize=False):
        # Retrieve the data item from the model
        plot_data_item = self._proxy_model.item_from_index(index)
        plot_data_item.visible = self._visible and visible

        if self.data_unit is not None:
            plot_data_item.data_unit = self.data_unit
            plot_data_item.spectral_axis_unit = self.spectral_axis_unit

        self.addItem(plot_data_item)

        if initialize:
            self._data_unit = plot_data_item.data_unit
            self._spectral_axis_unit = plot_data_item.spectral_axis_unit

            self._plot_item.setLabel('bottom', units=self.spectral_axis_unit)
            self._plot_item.setLabel('left', units=self.data_unit)

        # Emit a plot added signal
        self.plot_added.emit()

    def remove_plot(self, index, start=None, end=None):
        """
        Removes a plot data item given an index in the current plot sub
        window's proxy model.

        Parameters
        ----------
        index : :class:`~qtpy.QtCore.QModelIndex`
            The index in the model of the data item associated with this plot.
        start : int
            The starting index in the model item list.
        end : int
            The ending index in the model item list.
        """
        # Retrieve the data item from the proxy model
        plot_data_item = self.proxy_model.item_from_index(index)

        if plot_data_item is not None:
            # Remove plot data item from this plot
            self.removeItem(plot_data_item)

            # If there are no current plots, reset unit information for plot
            if len(self.listDataItems()) == 0:
                self._data_unit = None
                self._spectral_axis_unit = None

                self._plot_item.setLabel('bottom', units="")
                self._plot_item.setLabel('left', units="")

            # Emit a plot added signal
            self.plot_removed.emit()
