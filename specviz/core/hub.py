import logging

import astropy.units as u
from specutils.spectra.spectral_region import SpectralRegion

from .items import DataItem


class Hub:
    def __init__(self, workspace, *args, **kwargs):
        self._workspace = workspace

    @property
    def workspace(self):
        """The active workspace."""
        return self._workspace

    @property
    def model(self):
        """The data item model of the active workspace."""
        return self.workspace.model

    @property
    def proxy_model(self):
        """The proxy model of the active workspace."""
        return self.workspace.proxy_model

    @property
    def plot_window(self):
        """The currently selected plot window of the workspace."""
        return self.workspace.current_plot_window

    @property
    def plot_windows(self):
        """The currently selected plot window of the workspace."""
        return self.workspace.mdi_area.subWindowList()

    @property
    def plot_widget(self):
        """The plot widget of the currently active plot window."""
        return self.workspace.current_plot_window.plot_widget

    @property
    def plot_item(self):
        """The currently selected plot item."""
        if self.workspace is not None:
            return self.workspace.current_item

    @property
    def plot_items(self):
        """Returns the currently selected plot item."""
        return self.proxy_model.items

    @property
    def visible_plot_items(self):
        """Plotted data that are currently visible."""
        if self.plot_widget is not None:
            return self.plot_widget.listDataItems()

    @property
    def regions(self):
        """The currently active ROI on the plot."""
        return self.plot_window.plot_widget.list_all_regions()

    @property
    def spectral_regions(self):
        """
        Currently plotted ROIs returned as a
        :class:`~specutils.spectra.SpectralRegion`.
        """
        regions = self.regions

        if len(regions) == 0:
            return None

        units = u.Unit(self.plot_window.plot_widget.spectral_axis_unit or "")
        positions = []

        for region in regions:
            pos = (region.getRegion()[0] * units,
                   region.getRegion()[1] * units)

            if pos is not None:
                positions.append(pos)

        return SpectralRegion(positions)

    @property
    def selected_region(self):
        """The currently active ROI on the plot."""
        return self.plot_window.plot_widget.selected_region

    @property
    def selected_region_bounds(self):
        """The bounds of currently active ROI on the plot."""
        return self.plot_window.plot_widget.selected_region_bounds

    @property
    def data_item(self):
        """The data item of the currently selected plot item."""
        if self.plot_item is not None:
            return self.plot_item.data_item

    @property
    def data_items(self):
        """List of all data items held in the data item model."""
        return self.model.items

    def append_data_item(self, data_item):
        """
        Adds a new data item object to appear in the left data list view.

        Parameters
        ----------
        data_item : :class:`~specviz.core.items.PlotDataItem`
            The data item to be added to the list view.
        """
        if isinstance(data_item, DataItem):
            self.workspace.model.appendRow(data_item)
            self.workspace.model.data_added.emit(data_item)
        else:
            logging.error("Data item model only accepts items of class "
                          "'DataItem', received '{}'.".format(type(data_item)))

    def plot_data_item_from_data_item(self, data_item):
        """
        Returns the PlotDataItem associated with the provided DataItem.

        Parameters
        ----------
        data_item : :class:`~specviz.core.items.PlotDataItem`
            The DataItem from which the associated PlotDataItem will be
            returned.

        Returns
        -------
        plot_data_item : :class:`~specviz.core.items.PlotDataItem`
            The PlotDataItem wrapping the DataItem.
        """
        plot_data_item = self.workspace.proxy_model.item_from_id(
            data_item.identifier)

        return plot_data_item

    def set_active_plugin_bar(self, name=None, index=None):
        """
        Sets the currently displayed widget in the plugin side panel.

        Parameters
        ----------
        name : str, optional
            The displayed name of the widget in the tab title.
        index : int, optional
            The index of the widget in the plugin tab widget.
        """
        if name is None and index is None:
            return
        elif index is not None:
            self.workspace.plugin_tab_widget.setCurrentIndex(index)
        elif name is not None:
            for i in range(self.workspace.plugin_tab_widget.count()):
                if self.workspace.plugin_tab_widget.tabText(i) == name:
                    self.workspace.plugin_tab_widget.setCurrentIndex(i)