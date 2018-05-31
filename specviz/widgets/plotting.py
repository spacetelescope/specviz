import os
import numpy as np
import pyqtgraph as pg
import qtawesome as qta

from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction
from qtpy.QtCore import Signal, QObject, Property, QModelIndex
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
    plot_added = Signal()
    plot_removed = Signal()

    def __init__(self, name=None, model=None, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)

        self._name = name or "Untitled Plot"
        self._plot_item = self.getPlotItem()

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

        # Initialize all plots
        for i in range(len(self._proxy_model.sourceModel().items)):
            self.add_plot(self._proxy_model.index(i, 0), initialize=i == 0)

        self.setup_connections()

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

    def setup_connections(self):
        # Listen for model events to add/remove items from the plot
        self._proxy_model.rowsInserted.connect(self.add_plot)
        self._proxy_model.rowsAboutToBeRemoved.connect(self.remove_plot)

    def add_plot(self, index, first=None, last=None, initialize=False):
        # Retrieve the data item from the model
        plot_data_item = self._proxy_model.item_from_index(index)

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

    def remove_plot(self, index, first=None, last=None):
        # Retrieve the data item from the model
        plot_data_item = self._proxy_model.data(index)

        if plot_data_item is not None:
            # Remove plot data item from this plot
            self.removeItem(plot_data_item)

            # Emit a plot added signal
            self.plot_removed.emit()
