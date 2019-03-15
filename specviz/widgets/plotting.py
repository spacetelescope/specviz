import os
import logging
import os

import astropy.units as u
import pyqtgraph as pg
import pyqtgraph.exporters
import qtawesome as qta
from qtpy import compat
from qtpy.QtCore import QEvent, Signal
from qtpy.QtGui import QColor
from qtpy.QtWidgets import (QColorDialog, QMainWindow, QMdiSubWindow,
                            QMessageBox, QAction, QActionGroup, QToolButton, QMenu)
from qtpy.uic import loadUi

from .custom import LinearRegionItem
from ..core.items import PlotDataItem
from ..core.models import PlotProxyModel
from ..widgets.custom import PlotSizeDialog, ModifiedImageExporter

__all__ = ['PlotWindow', 'PlotWidget']


EXPORT_FILTERS = {
    "*.png": ModifiedImageExporter,
    "*.jpg": ModifiedImageExporter,
    "*.tiff": ModifiedImageExporter,
    "*.svg": pg.exporters.SVGExporter,
}


class PlotWindow(QMdiSubWindow):
    """
    Displayed plotting subwindow available in the ``QMdiArea``.
    """
    window_removed = Signal()
    color_changed = Signal(PlotDataItem, QColor)
    width_changed = Signal(int)

    def __init__(self, model, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)
        # Hide the icon in the title bar
        self.setWindowIcon(qta.icon('fa.circle', opacity=0))

        # The central widget of the sub window will be a main window so that it
        # can support having tab bars
        self._central_widget = QMainWindow()
        self.setWidget(self._central_widget)

        loadUi(os.path.join(os.path.dirname(__file__), "ui", "plot_window.ui"),
               self._central_widget)

        # The central widget of the main window widget will be the plot
        self._model = model
        self._current_item_index = None

        self._plot_widget = PlotWidget(model=self._model)
        self._plot_widget.plotItem.setMenuEnabled(False)

        self._central_widget.setCentralWidget(self._plot_widget)

        # Setup action group for interaction modes
        mode_group = QActionGroup(self.tool_bar)
        mode_group.addAction(self._central_widget.pan_mode_action)
        self._central_widget.pan_mode_action.setChecked(True)
        mode_group.addAction(self._central_widget.zoom_mode_action)

        def _toggle_mode(state):
            view_state = self.plot_widget.plotItem.getViewBox().state.copy()
            view_state.update({'mouseMode': pg.ViewBox.RectMode
                               if state else pg.ViewBox.PanMode})
            self.plot_widget.plotItem.getViewBox().setState(view_state)

        # Setup plot settings options menu
        self.plot_settings_button = self.tool_bar.widgetForAction(
            self._central_widget.plot_settings_action)
        self.plot_settings_button.setPopupMode(QToolButton.InstantPopup)

        self.plot_settings_menu = QMenu(self.plot_settings_button)
        self.plot_settings_button.setMenu(self.plot_settings_menu)

        self.color_change_action = QAction("Line Color")
        self.plot_settings_menu.addAction(self.color_change_action)

        self.line_width_menu = QMenu("Line Widths")
        self.plot_settings_menu.addMenu(self.line_width_menu)

        # Setup the line width plot setting options
        for i in range(1, 4):
            act = QAction(str(i), self.line_width_menu)
            self.line_width_menu.addAction(act)
            act.triggered.connect(lambda *args, size=i:
                                  self._on_change_width(size))

        # Setup connections
        self._central_widget.pan_mode_action.triggered.connect(
            lambda: _toggle_mode(False))
        self._central_widget.zoom_mode_action.triggered.connect(
            lambda: _toggle_mode(True))
        self._central_widget.linear_region_action.triggered.connect(
            self.plot_widget._on_add_linear_region)
        self._central_widget.remove_region_action.triggered.connect(
            self.plot_widget._on_remove_linear_region)
        self.color_change_action.triggered.connect(
            self._on_change_color)
        self._central_widget.export_plot_action.triggered.connect(
            self._on_export_plot)
        self._central_widget.reset_view_action.triggered.connect(
            lambda: self._on_reset_view())

    @property
    def tool_bar(self):
        """
        Return the tool bar for the embedded plot widget.
        """
        return self._central_widget.tool_bar

    @property
    def current_item(self):
        """
        The currently selected plot data item.
        """
        if self._current_item_index is not None:
            return self.proxy_model.item_from_index(self._current_item_index)

    @property
    def plot_widget(self):
        """
        Return the embedded plot widget
        """
        return self._plot_widget

    @property
    def proxy_model(self):
        """
        The proxy model defined in the internal plot widget.
        """
        return self.plot_widget.proxy_model

    def closeEvent(self, event):
        """
        Called by qt when window closes, upon which
        it emits the window_removed signal.

        Parameters
        ----------
        event :
            ignored in this implementation.
        """
        self.window_removed.emit()

    def _on_current_item_changed(self, current_idx, prev_idx):
        self._current_item_index = current_idx

    def _on_reset_view(self):
        """
        Resets the visible range of the plot taking into consideration only the
        PlotDataItem objects currently attached.
        """
        self.plot_widget.autoRange(
                items=[item for item in self.plot_widget.listDataItems()
                       if isinstance(item, PlotDataItem)])
        self.plot_widget.sigRangeChanged.emit(*self.plot_widget.viewRange())

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

        color = QColorDialog.getColor(options=QColorDialog.ShowAlphaChannel)

        if color.isValid():
            self.current_item.color = color.toRgb()
            self.color_changed.emit(self.current_item, self.current_item.color)

    def _on_change_width(self, size):
        self.plot_widget.change_width(size)
        self.width_changed.emit(size)

    def _on_export_plot(self):
        file_path, key = compat.getsavefilename(filters=";;".join(
            EXPORT_FILTERS.keys()))

        if key == '':
            return

        exporter = EXPORT_FILTERS[key](self.plot_widget.plotItem)

        # TODO: Current issue in pyqtgraph where the user cannot explicitly
        # define the output size. Fix incoming.

        # plot_size_dialog = PlotSizeDialog(self)
        # plot_size_dialog.height_line_edit.setText(
        #     str(int(exporter.params.param('height').value())))
        # plot_size_dialog.width_line_edit.setText(
        #     str(int(exporter.params.param('width').value())))
        #
        # if key != "*.svg":
        #     if plot_size_dialog.exec_():
        #         exporter.params.param('height').setValue(int(exporter.params.param('height').value()),
        #                                                  blockSignal=exporter.heightChanged)
        #         exporter.params.param('width').setValue(int(exporter.params.param('height').value()),
        #                                                  blockSignal=exporter.widthChanged)
        #     else:
        #         return

        exporter.export(file_path)


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

    Attributes
    ----------
    plot_added : None
        Fired when a plot data item has been added to the plot widget.
    plot_removed : None
        Fired when a plot data item has been removed from the plot widget.
    roi_moved : Signal
        Fired when region is moved. Delivers the range of region as tuple.
    roi_removed : Signal
        Fired when region is removed. Delivers the region removed.
    mouse_enterexit : Signal
        Fired when mouse enters or exits the window. Delivers the event type.
    """
    plot_added = Signal(PlotDataItem)
    plot_removed = Signal(PlotDataItem)
    roi_moved = Signal(u.Quantity)
    roi_removed = Signal(LinearRegionItem)
    mouse_enterexit = Signal(QEvent.Type)
    data_unit_changed = Signal(str)
    spectral_axis_unit_changed = Signal(str)

    def __init__(self, title=None, model=None, visible=True, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)
        self._title = title or "Untitled Plot"
        self._plot_item = self.getPlotItem()
        self._visible = visible

        # Performance enhancements
        # self.setDownsampling(auto=False)
        # self.setClipToView(True)
        # self.useOpenGL(True)

        # Define labels for axes
        self._plot_item.setLabel('bottom', text='')
        self._plot_item.setLabel('left', text='')

        # Store current select region
        self._selected_region = None

        # Setup select region labels
        self._region_text_item = pg.TextItem(color="k")
        self.addItem(self._region_text_item, ignoreBounds=True)
        self._region_text_item.setParentItem(self.getViewBox())

        # Removes ability to automatically change units to match science notation
        self.getAxis('bottom').enableAutoSIPrefix(False)
        self.getAxis('left').enableAutoSIPrefix(False)

        # Store the unit information for this plot. This is defined by the
        # first data set that gets plotted. All other data sets will attempt
        # to be converted to these units.
        self._data_unit = None
        self._spectral_axis_unit = None

        # Cache a reference to the model object that's attached to the parent
        self._proxy_model = PlotProxyModel(model)

        # Set default axes ranges
        self.setRange(xRange=(0, 1), yRange=(0, 1))
        self.enableAutoRange(True)

        # Show grid lines
        self.showGrid(x=True, y=True, alpha=0.05)

        # Listen for model events to add/remove items from the plot
        self.proxy_model.sourceModel().data_added.connect(self._check_unit_compatibility)
        self.proxy_model.rowsAboutToBeRemoved.connect(
            lambda idx: self.remove_plot(index=idx))

        self.plot_added.connect(self.check_plot_compatibility)
        self.plot_removed.connect(self.check_plot_compatibility)

    @property
    def title(self):
        """
        The title of the widget.
        """
        return self._title

    @property
    def proxy_model(self):
        """
        The proxy model being used by this plot widget.
        """
        return self._proxy_model

    @property
    def data_unit(self):
        """
        The current data unit used for displaying the spectrum.
        """
        return self._data_unit

    @property
    def spectral_axis_unit(self):
        """
        The current spectral axis unit used for displaying the spectrum.
        """
        return self._spectral_axis_unit

    @data_unit.setter
    def data_unit(self, value):
        for plot_data_item in self.listDataItems():
            if plot_data_item.is_data_unit_compatible(value):
                plot_data_item.data_unit = value

                # Re-initialize plot to update the displayed values and
                # adjust ranges of the displayed axes
                # TODO: Changed this to data_unit from spectral_axis_unit
                self.initialize_plot(data_unit=value)
            else:
                # Technically, this should not occur, but in the unforseen
                # case that it does, remove the plot and log an error
                self.remove_plot(item=plot_data_item)
                logging.error("Removing plot '%s' due to incompatible units "
                              "('%s' and '%s').",
                              plot_data_item.data_item.name,
                              plot_data_item.data_unit, value)

    def set_data_unit(self, unit):
        """
        Sets the data unit and emits a signal telling interested
        parties of the change.

        Parameters
        ----------
        unit : :class:`~astropy.units.Unit`
            The unit to which the data axis will be converted.
        """
        unit = u.Unit(unit).to_string()

        self.data_unit = unit
        self.data_unit_changed.emit(unit)

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

    def set_spectral_axis_unit(self, unit):
        """
        Sets the spectral axis unit and emits a signal telling interested
        parties of the change.

        Parameters
        ----------
        unit : :class:`~astropy.units.Unit`
            The unit to which the spectral axis will be converted.
        """
        unit = u.Unit(unit).to_string()

        self.spectral_axis_unit = unit
        self.spectral_axis_unit_changed.emit(unit)

    @property
    def selected_region(self):
        """
        The currently selected region object.
        """
        return self._selected_region

    @property
    def selected_region_bounds(self):
        """
        The bounds of the currently selected region as a tuple of
        `~astropy.units.Quantity` objects.
        """
        if self.selected_region is not None:
            return self.selected_region.getRegion() * u.Unit(
                self.spectral_axis_unit or "")

    def on_item_changed(self, item):
        """
        Called when the user clicks the item's checkbox.
        """
        source_index = self.proxy_model.sourceModel().indexFromItem(item)
        proxy_index = self.proxy_model.mapFromSource(source_index)

        plot_data_item = self.proxy_model.item_from_index(proxy_index)

        # Re-evaluate plot unit compatibilities
        self.check_plot_compatibility()

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

    def check_plot_compatibility(self):
        """
        Checks for unit compatibility between this plot widget and all plot
        data items currently in the proxy model. If an item is not compatible,
        its state is set to disabled and the user will not be able to plot it
        in the plot widget.
        """
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
                plot_data_item.visible = False
                plot_data_item.data_item.setEnabled(False)

    def _check_unit_compatibility(self, item):
        plot_data_item = self.proxy_model.item_from_id(item.identifier)

        if not plot_data_item.are_units_compatible(self.spectral_axis_unit,
                                                   self.data_unit):
            plot_data_item.data_item.setEnabled(False)

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
            item.visible = visible or self._visible

        if item.are_units_compatible(self.spectral_axis_unit,
                                               self.data_unit):
            item.data_unit = self.data_unit
            item.spectral_axis_unit = self.spectral_axis_unit
        else:
            item.reset_units()

        # Include uncertainty item
        if item.uncertainty is not None:
            self.addItem(item.error_bar_item)

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
        # Update any ROIs currently on the plot
        if spectral_axis_unit is not None:
            for item in self.items():
                if isinstance(item, LinearRegionItem):
                    item.setRegion(
                        u.Quantity(item.getRegion(), self.spectral_axis_unit).to(
                            spectral_axis_unit, equivalencies=u.spectral()).value)

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
        self.setDownsampling(auto=False)

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

            # Remove plot error bars
            if item.uncertainty is not None:
                self.removeItem(item.error_bar_item)

            # If there are no current plots, reset unit information for plot
            if len(self.listDataItems()) == 0:
                self._data_unit = None
                self._spectral_axis_unit = None

                self._plot_item.setLabel('bottom', "", units="")
                self._plot_item.setLabel('left', "", units="")

                # Reset the plot axes
                self.setRange(xRange=(0, 1), yRange=(0, 1))
            # elif len(self.listDataItems()) == 1:
            #     self.autoRange()

            # Emit a plot removed signal
            self.plot_removed.emit(item)

    def clear_plots(self):
        """
        Removes all plots from the plot widget.
        """
        for item in self.listDataItems():
            if isinstance(item, PlotDataItem):
                self.remove_plot(item=item)

    def _on_region_changed(self):
        """
        Updates the displayed minimum and maximum values when the currently
        selected region is changed.
        """
        self._region_text_item.setText(
            "Region: ({:0.5g}, {:0.5g})".format(*self.selected_region_bounds))

        # Check for color theme changes

        self.roi_moved.emit(self.selected_region_bounds)

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
        disp_range = disp_axis.range[1] - disp_axis.range[0]

        region = LinearRegionItem(
            values=(min_bound or (mid_point - disp_range*0.3),
                    max_bound or (mid_point + disp_range*0.3)))

        def _on_region_updated(new_region):
            # If the most recently selected region is already the currently
            # selected region, ignore and return
            if new_region == self._selected_region:
                return

            # De-select previous region
            if self._selected_region is not None:
                self._selected_region._on_region_selected(False)
                self._selected_region.sigRegionChangeFinished.disconnect(
                    self._on_region_changed)
                self._selected_region.selected.disconnect(
                    self._on_region_changed)

            new_region._on_region_selected(True)

            # Listen to region move events
            new_region.sigRegionChangeFinished.connect(
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
        roi = self._selected_region
        self.removeItem(self._selected_region)
        self._selected_region = None
        self._region_text_item.setText("")
        self.roi_removed.emit(roi)

    def list_all_regions(self):
        """Get all region items in plot"""
        regions = []

        for item in self.items():
            if isinstance(item, LinearRegionItem):
                regions.append(item)

        return regions

    def change_width(self, size):
        """
        Change the width of every plot data item rendered on the plot. This
        currently does not include uncertainty indicators.

        Notes
        -----
            Enabling a width greater than 1 will automatically enable opengl
            and use the user's gpu to render the plot. If the user has not
            set the global pyqtgraph opengl option to true, opengl will be
            disabled when the user returns the size to 1.

        Parameters
        ----------
        size : int
            The new width of the rendered lines.
        """
        if not pg.getConfigOption('useOpenGL'):
            self.useOpenGL(True if size > 1 else False)

        for item in self.items():
            if isinstance(item, PlotDataItem):
                item.width = size

    def enterEvent(self, event):
        """
        Intercept qt mode enter event and raise event type.

        Parameters
        ----------
        event : ``QMouseEvent``
            The intercepted event.
        """
        self.mouse_enterexit.emit(event.type())

    def leaveEvent(self, event):
        """
        Intercept qt mode enter event and raise event type.

        Parameters
        ----------
        event : ``QMouseEvent``
            The intercepted event.
        """
        self.mouse_enterexit.emit(event.type())
