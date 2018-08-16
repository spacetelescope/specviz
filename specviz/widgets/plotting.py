import logging
import os

import astropy.units as u
import numpy as np
import pyqtgraph as pg
import qtawesome as qta
from qtpy.QtCore import Property, QEvent, QModelIndex, QObject, Qt, Signal
from qtpy.QtWidgets import (QAction, QListWidget, QMainWindow, QMdiSubWindow, QDialog,
                            QToolButton, QSizePolicy, QWidget, QMenu, QWidgetAction, QColorDialog, QMessageBox)
from qtpy.uic import loadUi

from ..core.items import PlotDataItem
from ..core.models import PlotProxyModel
from ..utils import UI_PATH
from .custom import LinearRegionItem


class PlotWindow(QMdiSubWindow):
    """
    Displayed plotting subwindow available in the `QMdiArea`.
    """
    def __init__(self, model, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)

        # The central widget of the sub window will be a main window so that it
        # can support having tab bars
        self._central_widget = QMainWindow()
        self.setWidget(self._central_widget)

        loadUi(os.path.join(UI_PATH, "plot_window.ui"), self._central_widget)

        # The central widget of the main window widget will be the plot
        self._model = model
        self._current_item_index = None

        self._plot_widget = PlotWidget(model=self._model)
        self._plot_widget.plotItem.setMenuEnabled(False)

        self._central_widget.setCentralWidget(self._plot_widget)

        # Add a menu to the plot options action
        _plot_options_button = self._central_widget.tool_bar.widgetForAction(
            self._central_widget.plot_options_action)
        _plot_options_button.setPopupMode(QToolButton.InstantPopup)

        self._plot_options_menu = QMenu(self._central_widget)
        _plot_options_button.setMenu(self._plot_options_menu)

        # Add the line color action
        self._change_color_action = QAction("Line Color")
        self._plot_options_menu.addAction(self._change_color_action)

        # Add the qtawesome icons to the plot-specific actions
        self._central_widget.linear_region_action.setIcon(
            qta.icon('fa.compress',
                     color='black',
                     color_active='orange'))

        self._central_widget.remove_region_action.setIcon(
            qta.icon('fa.compress', 'fa.trash',
                      options=[{'scale_factor': 1},
                               {'color': 'red', 'scale_factor': 0.75,
                                'offset': (0.25, 0.25)}]))

        # self._main_window.rectangular_region_action.setIcon(
        #     qta.icon('fa.square',
        #              active='fa.legal',
        #              color='black',
        #              color_active='orange'))

        self._central_widget.plot_options_action.setIcon(
            qta.icon('fa.line-chart',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._central_widget.export_plot_action.setIcon(
            qta.icon('fa.download',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        spacer = QWidget()
        spacer.setFixedSize(self._central_widget.tool_bar.iconSize() * 2)
        self._central_widget.tool_bar.insertWidget(
            self._central_widget.plot_options_action, spacer)

        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        spacer.setSizePolicy(size_policy)
        self._central_widget.tool_bar.addWidget(spacer)

        # Setup connections
        self._central_widget.linear_region_action.triggered.connect(
            self.plot_widget._on_add_linear_region)
        self._central_widget.remove_region_action.triggered.connect(
            self.plot_widget._on_remove_linear_region)
        self._change_color_action.triggered.connect(self._on_change_color)

    @property
    def current_item(self):
        if self._current_item_index is not None:
            return self.proxy_model.item_from_index(self._current_item_index)

    @property
    def plot_widget(self):
        return self._plot_widget

    @property
    def proxy_model(self):
        return self.plot_widget.proxy_model

    def _on_current_item_changed(self, current_idx, prev_idx):
        self._current_item_index = current_idx

    def _on_change_color(self):
        """
        Listens for color changed events in plot windows, gets the currently
        selected item in the data list view, and changes the stored color
        value.
        """
        # If there is no currently selected rows, raise an error
        if self.current_item is None:
            message_box = QMessageBox()
            message_box.setText("No item selected, cannot change color.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "There is currently no item selected. Please select an item "
                "before changing its plot color.")

            message_box.exec()
            return

        color = QColorDialog.getColor()

        if color.isValid():
            self.current_item.color = color.name()

        # Emit a data change signal so that the list view can upate the
        # displayed color value for the model item
        self.proxy_model.dataChanged.emit(self._current_item_index,
                                          self._current_item_index)


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
        self._plot_item.setLabel('bottom', text='')
        self._plot_item.setLabel('left', text='')

        # Store current select region
        self._selected_region = None

        # Setup select region labels
        self._region_text_item = pg.TextItem(color="k")
        self.addItem(self._region_text_item)
        self._region_text_item.setParentItem(self.getViewBox())

        # Store the unit information for this plot. This is defined by the
        # first data set that gets plotted. All other data sets will attempt
        # to be converted to these units.
        self._data_unit = None
        self._spectral_axis_unit = None

        # Cache a reference to the model object that's attached to the parent
        self._proxy_model = PlotProxyModel(model)

        # Set default axes ranges
        self.setRange(xRange=(0, 1), yRange=(0, 1))

        # Listen for model events to add/remove items from the plot
        self.proxy_model.rowsInserted.connect(self._check_unit_compatibility)
        self.proxy_model.rowsAboutToBeRemoved.connect(
            lambda idx: self.remove_plot(index=idx))

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

    @property
    def spectral_axis_unit(self):
        return self._spectral_axis_unit

    @data_unit.setter
    def data_unit(self, value):
        for plot_data_item in self.listDataItems():
            if plot_data_item.is_data_unit_compatible(value):
                plot_data_item.data_unit = value

                # Re-initialize plot to update the displayed values and
                # adjust ranges of the displayed axes
                self.initialize_plot(spectral_axis_unit=value)
            else:
                # Technically, this should not occur, but in the unforseen
                # case that it does, remove the plot and log an error
                self.remove_plot(item=plot_data_item)
                logging.error("Removing plot '%s' due to incompatible units "
                              "('%s' and '%s').",
                              plot_data_item.data_item.name,
                              plot_data_item.spectral_axis_unit, value)

    @spectral_axis_unit.setter
    def spectral_axis_unit(self, value):
        for plot_data_item in self.listDataItems():
            if plot_data_item.is_spectral_axis_unit_compatible(value):
                plot_data_item.spectral_axis_unit = value

                # Re-initialize plot to update the displayed values and
                # adjust ranges of the displayed axes
                self.initialize_plot(spectral_axis_unit=value)
            else:
                # Technically, this should not occur, but in the unforseen
                # case that it does, remove the plot and log an error
                self.remove_plot(item=plot_data_item)
                logging.error("Removing plot '%s' due to incompatible units "
                              "('%s' and '%s').",
                              plot_data_item.data_item.name,
                              plot_data_item.spectral_axis_unit, value)

    def on_item_changed(self, item):
        """
        Called when the user clicks the item's checkbox.
        """
        source_index = self.proxy_model.sourceModel().indexFromItem(item)
        proxy_index = self.proxy_model.mapFromSource(source_index)

        plot_data_item = self.proxy_model.item_from_index(proxy_index)

        if plot_data_item.visible:
            if plot_data_item not in self.listDataItems():
                logging.info("Adding plot %s", item.name)
                self.add_plot(item=plot_data_item,
                              visible=True,
                              initialize=len(self.listDataItems()) == 0)
        else:
            if plot_data_item in self.listDataItems():
                logging.info("Removing plot %s", item.name)
                self.remove_plot(item=plot_data_item)

        # Re-evaluate plot unit compatibilities
        # self.check_plot_compatibility()

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

    def add_plot(self, item=None, index=None, visible=True, initialize=False):
        if item is None:
            # Retrieve the data item from the model
            item = self._proxy_model.item_from_index(index)
            item.visible = self._visible and visible

        if item.are_units_compatible(self.spectral_axis_unit,
                                               self.data_unit):
            item.data_unit = self.data_unit
            item.spectral_axis_unit = self.spectral_axis_unit
        else:
            item.reset_units()

        self.addItem(item)

        if initialize:
            self.initialize_plot(item.data_unit,
                                 item.spectral_axis_unit)

        # Emit a plot added signal
        self.plot_added.emit(item)

    def initialize_plot(self, data_unit=None, spectral_axis_unit=None):
        self._data_unit = data_unit or self._data_unit
        self._spectral_axis_unit = spectral_axis_unit or self._spectral_axis_unit

        # Deal with dispersion units
        dispersion_unit = u.Unit(self.spectral_axis_unit or "")

        if dispersion_unit.physical_type == 'length':
            self._plot_item.setLabel('bottom', "Wavelength", units=dispersion_unit)
        elif dispersion_unit.physical_type == 'frequency':
            self._plot_item.setLabel('bottom', "Frequency", units=dispersion_unit)
        elif dispersion_unit.physical_type == 'energy':
            self._plot_item.setLabel('bottom', "Energy", units=dispersion_unit)
        else:
            self._plot_item.setLabel('bottom', "Dispersion", units=dispersion_unit)

        # Deal with data units
        data_unit = u.Unit(self.data_unit or "")

        if data_unit.physical_type == 'spectral flux density':
            self._plot_item.setLabel('left', "Flux Density", units=data_unit)
        else:
            self._plot_item.setLabel('left', "Flux", units=data_unit)

        self.autoRange()

    def remove_plot(self, item=None, index=None, start=None, end=None):
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
        if item is None:
            if not index.isValid():
                return

            # Retrieve the data item from the proxy model
            item = self.proxy_model.item_from_index(index)

        if item is not None:
            # Since we've removed the plot, ensure that its visibility state
            # had been changed as well
            item.visible = False

            # Remove plot data item from this plot
            self.removeItem(item)

            # If there are no current plots, reset unit information for plot
            if len(self.listDataItems()) == 0:
                self._data_unit = None
                self._spectral_axis_unit = None

                self._plot_item.setLabel('bottom', "", units="")
                self._plot_item.setLabel('left', "", units="")

                # Reset the plot axes
                self.setRange(xRange=(0, 1), yRange=(0, 1))
            elif len(self.listDataItems()) == 1:
                self.autoRange()

            # Emit a plot added signal
            self.plot_removed.emit(item)

    def _on_region_changed(self):
        # When the currently select region is changed, update the displayed
        # minimum and maximum values
        self._region_text_item.setText(
            "Region: ({:0.5g}, {:0.5g})".format(
                *(self._selected_region.getRegion() *
                  u.Unit(self.spectral_axis_unit or ""))
                ))

    def _on_add_linear_region(self):
        """
        Create a new region and add it to the plot widget.
        """
        disp_axis = self.getAxis('bottom')
        mid_point = disp_axis.range[0] + (disp_axis.range[1] - disp_axis.range[0]) * 0.5
        region = LinearRegionItem(values=(disp_axis.range[0] + mid_point * 0.75,
                                          disp_axis.range[1] - mid_point * 0.75))

        def _on_region_updated(new_region):
            # If the most recently selected region is already the currently
            # selected region, ignore and return
            if new_region == self._selected_region:
                return

            # De-select previous region
            if self._selected_region is not None:
                self._selected_region._on_region_selected(False)

            new_region._on_region_selected(True)

            # Listen to region move events
            new_region.sigRegionChanged.connect(
                self._on_region_changed)
            new_region.selected.connect(
                self._on_region_changed)

            # Set the region as the currently selected region
            self._selected_region = new_region

        # When this region is selected, update the stored pointer to the
        # current region and the displayed region bounds
        region.selected.connect(lambda: _on_region_updated(region))
        region.selected.emit(True)

        self.addItem(region)

        # Display the bounds in the upper-left hand corner of the plot
        self._on_region_changed()

    def _on_remove_linear_region(self):
        self.removeItem(self._selected_region)
        self._selected_region = None
        self._region_text_item.setText("")
