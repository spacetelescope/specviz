import os
import numpy as np
import pyqtgraph as pg
import qtawesome as qta

from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction
from qtpy.QtCore import Signal
from qtpy.uic import loadUi

from ..utils import UI_PATH


class PlotWindow(QMdiSubWindow):
    def __init__(self, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)

        # The central widget of the sub window will be a main window so that it
        # can support having tab bars
        self._main_window = QMainWindow()
        self.setWidget(self._main_window)

        loadUi(os.path.join(UI_PATH, "plot_window.ui"), self._main_window)

        # The central widget of the main window widget will be the plot
        self._model = self.parent().model
        self._plot_widget = PlotWidget(model=self.parent().model)
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

        self.setup_connections()

    def setup_connections(self):
        def change_color():
            model = self._model
            data_item = model.items[0]
            print("Changing color on", data_item.name)
            data_item.color = '#000000'

        self._main_window.plot_options_action.triggered.connect(change_color)


class PlotWidget(pg.PlotWidget):
    plot_added = Signal()
    plot_removed = Signal()

    def __init__(self, name=None, model=None, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)

        self._name = name or "Untitled Plot"

        # Store the unit information for this plot. This is defined by the
        # first data set that gets plotted. All other data sets will attempt
        # to be converted to these units.
        self._data_unit = None
        self._spectral_axis_unit = None

        # Cache a reference to the model object that's attached to the parent
        self._model = model

        # Plot current data items that exist in the model
        for item in self._model.items:
            plot_data_item = PlotDataItem(item)
            self.addItem(plot_data_item)

        self.setup_connections()

    @property
    def name(self):
        return self._name

    def setup_connections(self):
        # Listen for model events to add/remove items from the plot
        self._model.rowsInserted.connect(self.add_plot)
        self._model.rowsAboutToBeRemoved.connect(self.remove_plot)

    def add_plot(self, index, first, last):
        # Retrieve the data item from the model
        data_item = self._model.data(index)

        # Create new plot data item and add it to this plot
        plot_data_item = PlotDataItem(data_item)
        self.addItem(plot_data_item)

        # Emit a plot added signal
        self.plot_added.emit()

    def remove_plot(self, index, first, last):
        # Retrieve the data item from the model
        data_item = self._model.data(index)

        # Find the plot data item associated with this data item
        plot_data_item = next((x for x in self.items), None)

        if plot_data_item is not None:
            # Remove plot data item from this plot
            self.removeItem(plot_data_item)

            # Emit a plot added signal
            self.plot_removed.emit()


class PlotDataItem(pg.PlotDataItem):
    data_unit_changed = Signal(str)
    spectral_axis_unit_changed = Signal(str)

    def __init__(self, data_item, *args, **kwargs):
        super(PlotDataItem, self).__init__(*args, **kwargs)

        self._data_item = data_item

        # Set data
        self.set_data()
        self.setPen(color=self._data_item.color)

        # Connect slots to data item signals
        self._data_item.flux_unit_changed.connect(self.set_data)
        self._data_item.spectral_axis_unit_changed.connect(self.set_data)

        # Connect to color signals
        self._data_item.color_changed.connect(lambda c: self.setPen(color=c))

    def update_data(self):
        # Replot data
        self.setData(self._data_item.spectral_axis, self._data_item.flux)

    def set_data(self):
        self.setData(self._data_item.spectral_axis, self._data_item.flux)