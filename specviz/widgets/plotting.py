import os

import astropy.units as u
import numpy as np
import logging
import pyqtgraph as pg
import qtawesome as qta

from qtpy.QtCore import Property, QEvent, QModelIndex, QObject, Qt, Signal
from qtpy.QtWidgets import (QAction, QListWidget, QMainWindow, QMdiSubWindow,
                            QMenu, QSizePolicy, QWidget, QDialog, QDialogButtonBox,
                            QToolButton, QWidgetAction, QColorDialog, QMessageBox)
from qtpy.uic import loadUi

from ..core.items import PlotDataItem
from ..core.models import PlotProxyModel
from ..utils import UI_PATH
from .custom import LinearRegionItem

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

        self._main_window.change_unit_action.setIcon(
            qta.icon('fa.exchange',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self.setup_connections()
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

    def setup_connections(self):
        def change_color():
            model = self._model
            data_item = model.items[0]
            print("Changing color on", data_item.name)
            data_item.color = '#000000'

        self._main_window.plot_options_action.triggered.connect(change_color)
        self._main_window.change_unit_action.triggered.connect(self._on_change_unit)

    def _on_change_unit(self):
        # print(self.current_item, self._plot_widget)
        unit_change = UnitChangeDialog(self._plot_widget)
        unit_change.exec_()

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

    # def set_data_unit(self, data_unit):
    #     self._data_unit = data_unit

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
        """
        Adds a plot data item given an index in the current plot sub
        window's proxy model, or if given the item explicitly.

        Parameters
        ----------
        item : :class:`~specviz.core.items.PlotDataItem`
            The item in the proxy model to add to this plot.
        index : :class:`~qtpy.QtCore.QModelIndex`
            The index in the model of the data item associated with this plot.
        visible : bool
            Sets the initial visibility state of this plot item.
        initialize : bool
            Whether the plot should re-evaluate axis labels and re-configure
            axis bounds.
        """
        if item is None:
            # Retrieve the data item from the model
            item = self._proxy_model.item_from_index(index)
            item.visible = self._visible

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
        """
        Routine to re-configure the display settings of the plot to fit the
        plotted data and re-assess the physical type and unit information of
        the data.

        Parameters
        ----------
        data_unit : str or :class:`~astropy.units.Unit`
            The data unit used for the display of the y axis.
        spectral_axis_unit : str or :class:`~astropy.units.Unit`
            The spectral axis unit used for the display of the x axis.
        """
        # We need to be careful here to explicitly check the data_unit against
        # None since it may also be '' which is a valid dimensionless unit.
        self._data_unit = self._data_unit if data_unit is None else data_unit
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
        item : :class:`~specviz.core.items.PlotDataItem`
            The item in the proxy model to remove from this plot.
        index : :class:`~qtpy.QtCore.QModelIndex`
            The index in the model of the data item associated with this plot.
        start : int
            The starting index in the model item list.
        end : int
            The ending index in the model item list.
        """
        if item is None and index is not None:
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
        """
        Updates the displayed minimum and maximum values when the currently
        selected region is changed.
        """
        self._region_text_item.setText(
            "Region: ({:0.5g}, {:0.5g})".format(
                *(self._selected_region.getRegion() *
                  u.Unit(self.spectral_axis_unit or ""))
                ))

    def _on_add_linear_region(self, min_bound=None, max_bound=None):
        """
        Create a new region and add it to the plot widget. If no bounds are
        given, region is placed around the middle 50 percent of the displayed
        spectral axis.

        Parameters
        ----------
        min_bound : float
            Placement of the left edge of the region in axis units.
        max_bound : float
            Placement of the right edge of the region in axis units.
        """
        disp_axis = self.getAxis('bottom')
        mid_point = disp_axis.range[0] + (disp_axis.range[1] -
                                          disp_axis.range[0]) * 0.5
        region = LinearRegionItem(
            values=(min_bound or disp_axis.range[0] + mid_point * 0.75,
                    max_bound or disp_axis.range[1] - mid_point * 0.75))

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
        """Remove the selected linear region from the plot."""
        self.removeItem(self._selected_region)
        self._selected_region = None
        self._region_text_item.setText("")

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
        self._units_titles = list(unit.long_names[0].title() for unit in self._units)

        # Holder values for current data unit and spectral axis unit
        self.current_data_unit = self._units_titles[0]
        self.current_spectral_axis_unit = self._units_titles[0]
        self.plot_widget = plot_widget

        # If the units in PlotWidget are not set, do not allow the user to click the OK button
        if self.plot_widget and self.plot_widget.data_unit and self.plot_widget.spectral_axis_unit:
            try:
                # Set the current data units to be the ones in plot_widget
                self.current_data_unit = u.Unit(self.plot_widget.data_unit).long_names[0].title()

                # Add current unit used by PlotWidget to the list [self._units] that fills the combobox
                if u.Unit(self.plot_widget.data_unit) not in self._units and \
                        self.current_data_unit not in self._units_titles:
                    self._units.append(u.Unit(self.plot_widget.data_unit))
                    self._units_titles.append(self.current_data_unit)

            except Exception as e:
                log.error(e)
                self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
                
            try:
                # Set the current spectral_axis unit to be the ones in plot_widget
                self.current_spectral_axis_unit = u.Unit(self.plot_widget.spectral_axis_unit).long_names[0].title()

                # Add current unit used by PlotWidget to the list [self._units] that fills the combobox
                if u.Unit(self.plot_widget.spectral_axis_unit) not in self._units and \
                        self.current_spectral_axis_unit not in self._units_titles:
                    self._units.append(u.Unit(self.plot_widget.spectral_axis_unit))
                    self._units_titles.append(self.current_spectral_axis_unit)

            except Exception as e:
                log.error(e)
                self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
                
        else:
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        # This gives the user the option to use their own units. These units are checked by u.Unit()
        # and PlotDataItem.is_spectral_axis_unit_compatible(spectral_axis_unit) and
        # PlotDataItem.is_data_unit_compatible(data_unit)
        self._units_titles.append("Custom")

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the PyQt UI for this dialog."""
        # Find the current unit in the list used to fill the combobox and set it as the current text
        self.ui.comboBox_spectral.addItems(self._units_titles)
        index = self._units_titles.index(self.current_spectral_axis_unit)
        self.ui.comboBox_spectral.setCurrentIndex(index) if index > 0 else False
        self.ui.label_convert_spectral.setText("Convert X axis units from {} to: ".format(self.current_spectral_axis_unit))

        # Find the current unit in the list used to fill the combobox and set it as the current text
        self.ui.comboBox_units.addItems(self._units_titles)
        index = self._units_titles.index(self.current_data_unit)
        self.ui.comboBox_units.setCurrentIndex(index) if index > 0 else False
        self.ui.label_convert_units.setText("Convert Y axis units from {} to: ".format(self.current_data_unit))

        # Hide custom unit options until it is chosen in the combobox
        self.ui.line_custom_spectral.hide()
        self.ui.label_valid_spectral.hide()

        self.ui.line_custom_units.hide()
        self.ui.label_valid_units.hide()

        # TODO: Implement option to preview the effect unit change will have on data
        self.ui.label_preview.hide()
        self.ui.label_preview_values.hide()

    def setup_connections(self):
        """Setup signal/slot connections for this dialog."""
        self.ui.comboBox_spectral.currentTextChanged.connect(lambda: self.on_combobox_change("X"))
        self.ui.line_custom_spectral.textChanged.connect(lambda: self.on_line_custom_units_change("X"))
        
        self.ui.comboBox_units.currentTextChanged.connect(lambda: self.on_combobox_change("Y"))
        self.ui.line_custom_units.textChanged.connect(lambda: self.on_line_custom_units_change("Y"))

        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.on_accepted)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.on_canceled)

    def on_combobox_change(self, axis):
        """Called when the text of the unit combo box has changed."""
        # If 'Custom', show validation label and line for entering units
        # The X axis corresponds to plot_data_item.spectral_axis_unit
        # The Y axis corresponds to plot_data_item.data_unit
        if axis == "X":
            combobox = self.ui.comboBox_spectral
            line_custom = self.ui.line_custom_spectral
            label_valid = self.ui.label_valid_spectral
        elif axis == "Y":
            combobox = self.ui.comboBox_units
            line_custom = self.ui.line_custom_units
            label_valid = self.ui.label_valid_units

        if combobox.currentText() == "Custom":
            line_custom.show()
            label_valid.show()
            label_valid.setText("Enter custom units")
            label_valid.setStyleSheet('color: green')

        else:
            line_custom.hide()
            label_valid.hide()

    def on_line_custom_units_change(self, axis):
        """Called when the text of the custom units textbox has changed."""
        # The X axis corresponds to plot_data_item.spectral_axis_unit
        # The Y axis corresponds to plot_data_item.data_unit
        if axis == "X":
            line_custom = self.ui.line_custom_spectral
            label_valid = self.ui.label_valid_spectral
        elif axis == "Y":
            line_custom = self.ui.line_custom_units
            label_valid = self.ui.label_valid_units

        # If Unit enter line is empty
        if line_custom.text() in ["", " "]:
            label_valid.setText("Enter custom units")
            label_valid.setStyleSheet('color: green')

            # Does not allow user to enter multiple spaces as valid unit
            if line_custom.text() == " ":
                line_custom.setText("")
            return

        # Try to enter the custom units
        try:
            u.Unit(line_custom.text())
            label_valid.setStyleSheet('color: green')
            label_valid.setText("{} is Valid".format(line_custom.text()))

        except Exception as e:
            # Take error message, break it up, and take the suggestions part and show it to the user
            log.debug(e)
            err = str(e)
            if "Did you mean " in err:
                similar_valid_units = err.split("Did you mean ")[1][:-1]
                label_valid.setText("Invalid, try: {}".format(similar_valid_units))
            else:
                label_valid.setText("Invalid")

            label_valid.setStyleSheet('color: red')

    def on_accepted(self):
        """Called when the user clicks the "Ok" button of the dialog."""
        if self.ui.comboBox_units.currentText() == "Custom":
            
            # Try to enter the custom units
            try:
                u.Unit(self.ui.line_custom_units.text())
            except Exception as e:
                log.warning("DID NOT CHANGE UNITS. {}".format(e))
                self.close()
                return False

            # If there are no units, just close the dialog and return False
            if self.ui.line_custom_units.text() in ["", " "]:
                log.warning("No custom units entered, units did not change")
                self.close()
                return False

            # Converts the data_unit to something that can be used by PlotWidget
            self.current_data_unit = self.line_custom_units.text()
            data_unit_formatted = u.Unit(self.current_data_unit).to_string()

            # Checks to make sure data_unit is compatible
            for plot_data_item in self.plot_widget.listDataItems():
                if not plot_data_item.is_data_unit_compatible(data_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(data_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.plot_widget.data_unit = data_unit_formatted

        else:
            # Converts the data_unit to something that can be used by PlotWidget
            self.current_data_unit = self.ui.comboBox_units.currentText()
            current_data_unit_in_u = self._units[self._units_titles.index(self.current_data_unit)]
            data_unit_formatted = u.Unit(current_data_unit_in_u).to_string()

            # Checks to make sure data_unit is compatible
            for plot_data_item in self.plot_widget.listDataItems():
                if not plot_data_item.is_data_unit_compatible(data_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(data_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.plot_widget.data_unit = data_unit_formatted

        if self.ui.comboBox_spectral.currentText() == "Custom":

            # Try to enter the custom units
            try:
                u.Unit(self.ui.line_custom_spectral.text())
            except Exception as e:
                log.warning("DID NOT CHANGE UNITS. {}".format(e))
                self.close()
                return False

            # If there are no units, just close the dialog and return False
            if self.ui.line_custom_spectral.text() in ["", " "]:
                log.warning("No custom units entered, units did not change")
                self.close()
                return False

            # Converts the spectral_axis_unit to something that can be used by PlotWidget
            self.current_spectral_axis_unit = self.line_custom_spectral.text()
            spectral_axis_unit_formatted = u.Unit(self.current_spectral_axis_unit).to_string()

            # Checks to make sure spectral_axis_unit is compatible
            for plot_data_item in self.plot_widget.listDataItems():
                if not plot_data_item.is_spectral_axis_unit_compatible(spectral_axis_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(spectral_axis_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.plot_widget.spectral_axis_unit = spectral_axis_unit_formatted

        else:
            # Converts the spectral_axis_unit to something that can be used by PlotWidget
            self.current_spectral_axis_unit = self.ui.comboBox_spectral.currentText()
            current_spectral_axis_unit_in_u = self._units[self._units_titles.index(self.current_spectral_axis_unit)]
            spectral_axis_unit_formatted = u.Unit(current_spectral_axis_unit_in_u).to_string()

            # Checks to make sure spectral_axis_unit is compatible
            for plot_data_item in self.plot_widget.listDataItems():
                if not plot_data_item.is_spectral_axis_unit_compatible(spectral_axis_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(spectral_axis_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.plot_widget.spectral_axis_unit = spectral_axis_unit_formatted

        self.close()
        return True

    def on_canceled(self):
        """Called when the user clicks the "Cancel" button of the dialog."""
        self.close()
