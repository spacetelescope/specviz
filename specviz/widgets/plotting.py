import os

import numpy as np
import logging
import pyqtgraph as pg
import qtawesome as qta
from astropy import units as u

from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog, QDialogButtonBox
from qtpy.QtCore import Property, QModelIndex, QObject, Qt, Signal, QEvent
from qtpy.QtWidgets import QAction, QListWidget, QMainWindow, QMdiSubWindow, QMenu, QWidget, QSizePolicy
from qtpy.uic import loadUi

from ..core.models import PlotProxyModel
from ..core.items import PlotDataItem
from ..utils import UI_PATH

logging.basicConfig(level=logging.DEBUG, format="%(filename)s: %(levelname)8s %(message)s")
log = logging.getLogger('UnitChangeDialog')
log.setLevel(logging.WARNING)


class PlotWindow(QMdiSubWindow):
    """
    Displayed plotting subwindow available in the `QMdiArea`.
    """
    def __init__(self, model, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)

        # The central widget of the sub window will be a main window so that it
        # can support having tab bars
        self._main_window = QMainWindow()
        self.setWidget(self._main_window)

        # Store all available rois on this plot
        self._rois = []

        loadUi(os.path.join(UI_PATH, "plot_window.ui"), self._main_window)

        # The central widget of the main window widget will be the plot
        self._model = model

        self._plot_widget = PlotWidget(model=self._model)
        self._plot_widget.plotItem.setMenuEnabled(False)
        self._main_window.setCentralWidget(self._plot_widget)

        self._plot_options_menu = QMenu(self)
        self._change_line_color = QAction("Line Color", self)
        self._plot_options_menu.addAction(self._change_line_color)

        self._main_window.plot_options_action.setMenu(self._plot_options_menu)

        # Add the qtawesome icons to the plot-specific actions
        self._main_window.linear_region_action.setIcon(
            qta.icon('fa.compress',
                     color='black',
                     color_active='orange'))

        self._main_window.remove_region_action.setIcon(
            qta.icon('fa.compress', 'fa.trash',
                      options=[{'scale_factor': 1},
                               {'color': 'red', 'scale_factor': 0.75,
                                'offset': (0.25, 0.25)}]))

        # self._main_window.rectangular_region_action.setIcon(
        #     qta.icon('fa.square',
        #              active='fa.legal',
        #              color='black',
        #              color_active='orange'))

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

        self._main_window.change_unit_action.setIcon(
            qta.icon('fa.exchange',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self.setup_connections()
        spacer = QWidget()
        spacer.setFixedSize(self._main_window.tool_bar.iconSize() * 2)
        self._main_window.tool_bar.insertWidget(
            self._main_window.plot_options_action, spacer)

        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        spacer.setSizePolicy(size_policy)
        self._main_window.tool_bar.addWidget(spacer)

    @property
    def plot_widget(self):
        return self._plot_widget

    def setup_connections(self):
        def change_color():
            model = self._model
            data_item = model.items[0]
            print("Changing color on", data_item.name)
            data_item.color = '#000000'

        self._main_window.plot_options_action.triggered.connect(change_color)
        self._main_window.change_unit_action.triggered.connect(self._on_change_unit)

    def _on_change_unit(self):
        unit_change = UnitChangeDialog(self._plot_widget)
        unit_change.exec_()

    @property
    def proxy_model(self):
        return self.plot_widget.proxy_model


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
    title : str
        The title of this particular plot window.
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
    plot_added = Signal(PlotDataItem)
    plot_removed = Signal(PlotDataItem)

    def __init__(self, title=None, model=None, visible=True, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self._title = title or "Untitled Plot"
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
        self.proxy_model.rowsInserted.connect(self._check_unit_compatibility)
        self.proxy_model.rowsAboutToBeRemoved.connect(self.remove_plot)

        self.plot_added.connect(self.check_plot_compatibility)
        self.plot_removed.connect(self.check_plot_compatibility)

    @property
    def title(self):
        return self._title

    @property
    def proxy_model(self):
        return self._proxy_model

    @property
    def data_unit(self):
        return self._data_unit

    def set_data_unit(self, data_unit):
        self._data_unit = data_unit

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

    def check_plot_compatibility(self):
        for i in range(self.proxy_model.sourceModel().rowCount()):
            model_item = self.proxy_model.sourceModel().item(i)
            source_index = self.proxy_model.sourceModel().indexFromItem(model_item)
            proxy_index = self.proxy_model.mapFromSource(source_index)

            if not proxy_index.isValid():
                continue

            plot_data_item = self.proxy_model.item_from_index(proxy_index)

            if self.data_unit is None and self.spectral_axis_unit is None or \
                    plot_data_item.are_units_compatible(
                        self.spectral_axis_unit, self.data_unit):
                plot_data_item.data_item.setEnabled(True)
            else:
                plot_data_item.data_item.setEnabled(False)

    def _check_unit_compatibility(self, index, first=None, last=None):
        if not index.isValid():
            return

        plot_data_item = self.proxy_model.item_from_index(index)

        if not plot_data_item.are_units_compatible(self.spectral_axis_unit,
                                                   self.data_unit):
            plot_data_item.setEnabled(False)

    def add_plot(self, index, first=None, last=None, visible=True,
                 initialize=False):
        # Retrieve the data item from the model
        plot_data_item = self._proxy_model.item_from_index(index)

        # Don't add a new data item if this one already exists
        if plot_data_item in self.listDataItems():
            return

        plot_data_item.visible = self._visible and visible

        if plot_data_item.are_units_compatible(self.spectral_axis_unit,
                                               self.data_unit):
            plot_data_item.data_unit = self.data_unit
            plot_data_item.spectral_axis_unit = self.spectral_axis_unit
        else:
            plot_data_item.reset_units()

        print("plot_data_item: ", plot_data_item.data_unit)

        self.addItem(plot_data_item)

        if initialize:
            self.set_units(plot_data_item.data_unit, plot_data_item.spectral_axis_unit)
            # self._data_unit = plot_data_item.data_unit
            # self._spectral_axis_unit = plot_data_item.spectral_axis_unit
            #
            # self._plot_item.setLabel('bottom', units=self.spectral_axis_unit)
            # self._plot_item.setLabel('left', units=self.data_unit)
            #
            # self.autoRange()

        # Emit a plot added signal
        self.plot_added.emit(plot_data_item)

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
        if not index.isValid():
            return

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

                # Reset the plot axes
                self.setRange(xRange=(0, 1), yRange=(0, 1))
            elif len(self.listDataItems()) == 1:
                self.autoRange()

            # Emit a plot added signal
            # self.plot_removed.emit()
            self.plot_removed.emit(plot_data_item)

    def set_units(self, data_unit, spectral_axis_unit):
        self._data_unit = data_unit
        self._spectral_axis_unit = spectral_axis_unit

        self._plot_item.setLabel('bottom', units=self.spectral_axis_unit)
        self._plot_item.setLabel('left', units=self.data_unit)

        self.autoRange()

class UnitChangeDialog(QDialog):
    def __init__(self, plot_widget, *args, **kwargs):
        super(UnitChangeDialog, self).__init__(*args, **kwargs)

        # Load the ui dialog
        self.ui = loadUi(os.path.join(UI_PATH, "unit_change_dialog.ui"), self)

        # Load Units to be used in combobox (plus a Custom option)
        self._units = [u.m, u.cm, u.mm, u.um, u.nm, u.AA]
        self._units_titles = list(unit.long_names[0].title() for unit in self._units) + ["Custom"]
        self.current_units = self._units_titles[0]
        self.plot_widget = plot_widget

        if self.plot_widget.data_unit:
            print("plot_widget", self.plot_widget.data_unit, u.Unit(self.plot_widget.data_unit))
            try:
                self.current_units = u.Unit(self.plot_widget.data_unit).long_names[0].title()
            except Exception as e:
                log.error(e)
                self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.setup_ui()
        self.setup_connections()

        """
        Check if data_units exist, if not make ok button not enabled.
        Make sure data_units are valid units, if not, log error and ok not enabled
        Add units to combobox
        change current_units to those units
        
        once unit is changed, emit signal to plot_widget
        """


    def setup_ui(self):
        """Setup the PyQt UI for this dialog."""
        self.ui.comboBox_units.addItems(self._units_titles)
        self.ui.label_convert.setText("Convert Units from {} to: ".format(self.current_units))

        self.ui.line_custom.hide()
        self.ui.label_valid_units.hide()

    def setup_connections(self):
        """Setup signal/slot connections for this dialog."""
        self.ui.comboBox_units.currentTextChanged.connect(self.on_combobox_change)
        self.ui.line_custom.textChanged.connect(self.on_line_custom_change)

        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.on_accepted)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.on_canceled)

    def on_combobox_change(self):
        """Called when the text of the unit combo box has changed."""
        # If 'Custom', show validation label and line for entering units
        if self.ui.comboBox_units.currentText() == "Custom":
            self.ui.line_custom.show()
            self.ui.label_valid_units.show()
            self.ui.label_valid_units.setText("Enter custom units")
            self.ui.label_valid_units.setStyleSheet('color: green')

        else:
            self.ui.line_custom.hide()
            self.ui.label_valid_units.hide()

    def on_line_custom_change(self):
        """Called when the text of the custom units textbox has changed."""
        # If Unit enter line is empty
        if self.ui.line_custom.text() in ["", " "]:
            self.ui.label_valid_units.setText("Enter custom units")
            self.ui.label_valid_units.setStyleSheet('color: green')

            # Does not allow user to enter multiple spaces as valid unit
            if self.ui.line_custom.text() == " ":
                self.ui.line_custom.setText("")
            return

        # Try to enter the custom units
        try:
            u.Unit(self.ui.line_custom.text())
            self.ui.label_valid_units.setStyleSheet('color: green')
            self.ui.label_valid_units.setText("{} is Valid".format(self.ui.line_custom.text()))

        except Exception as e:
            # Take error message, break it up, and take the suggestions part
            log.debug(e)
            err = str(e)
            if "Did you mean " in err:
                similar_valid_units = err.split("Did you mean ")[1][:-1]
                self.ui.label_valid_units.setText("Invalid, try: {}".format(similar_valid_units))
            else:
                self.ui.label_valid_units.setText("Invalid")

            self.ui.label_valid_units.setStyleSheet('color: red')

    def on_accepted(self):
        """Called when the user clicks the "Ok" button of the dialog."""
        if self.ui.comboBox_units.currentText() == "Custom":
            
            # Try to enter the custom units
            try:
                u.Unit(self.ui.line_custom.text())
            except Exception as e:
                log.warning("DID NOT CHANGE UNITS. {}".format(e))
                self.close()
                return False

            # If there are no units, just close the dialog and return False
            if self.ui.line_custom.text() in ["", " "]:
                log.warning("No custom units entered, units did not change")
                self.close()
                return False

            self.current_units = self.line_custom.text()
            # TODO: emit signal to plot_widget.data_unit when units are changed
            # self.plot_widget.set_data_unit(u.Unit(self.current_units))
            self.plot_widget.set_units(u.Unit(self.current_units), u.Unit(self.current_units))

        else:
            self.current_units = self.ui.comboBox_units.currentText()
            # TODO: emit signal to plot_widget.data_unit when units are changed
            current_unit_in_u = self._units[self._units_titles.index(self.current_units)]
            self.plot_widget.set_units(current_unit_in_u, current_unit_in_u)

        self.close()
        return True

    def on_canceled(self):
        """Called when the user clicks the "Cancel" button of the dialog."""
        self.close()
