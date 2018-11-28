import os
import logging
import numpy as np

from astropy import units as u

from specutils.spectra.spectrum1d import Spectrum1D
from specutils.spectra.spectral_region import SpectralRegion
from specutils.manipulation import extract_region
from specutils.analysis import snr, equivalent_width, fwhm, centroid, line_flux

from qtpy.QtWidgets import QWidget
from qtpy.uic import loadUi
from qtpy.QtGui import QIcon

from ...core.items import PlotDataItem
from ...utils.helper_functions import format_float_text
from ...core.plugin import plugin


"""
The next three functions are place holders while specutils is updated to handle
these computations internally. They will be moved into the StatisticsWidget
once they are updated.
"""
def check_unit_compatibility(spec, region):
    spec_unit = spec.spectral_axis.unit
    if region.lower is not None:
        region_unit = region.lower.unit
    elif region.upper is not None:
        region_unit = region.upper.unit
    else:
        return False
    return spec_unit.is_equivalent(region_unit)


def clip_region(spectrum, region):
    # If the region is out of data range return None:
    if region.lower > spectrum.spectral_axis.max() or \
            region.upper < spectrum.spectral_axis.min():
        return None

    # Clip region. There is currently no way to update
    # SpectralRegion lower and upper so we have to create
    # a new object here.
    lower = max(region.lower, spectrum.spectral_axis.min())
    upper = min(region.upper, spectrum.spectral_axis.max())

    return SpectralRegion(lower, upper)


def compute_stats(spectrum):
    """
    Compute basic statistics for a spectral region.
    Parameters
    ----------
    spectrum : `~specutils.spectra.spectrum1d.Spectrum1D`
    region: `~specutils.utils.SpectralRegion`
    """

    try:
        cent = centroid(spectrum, region=None) # we may want to adjust this for continuum subtraction
    except Exception as e:
        logging.debug(e)
        cent = "Error"

    try:
        snr_val = snr(spectrum)
    except Exception as e:
        logging.debug(e)
        snr_val = "N/A"

    try:
        fwhm_val = fwhm(spectrum)
    except Exception as e:
        logging.debug(e)
        fwhm_val = "Error"

    try:
        ew = equivalent_width(spectrum)
    except Exception as e:
        logging.debug(e)
        ew = "Error"

    try:
        total = line_flux(spectrum)
    except Exception as e:
        logging.debug(e)
        total = "Error"

    return {'mean': spectrum.flux.mean(),
            'median': np.median(spectrum.flux),
            'stddev': spectrum.flux.std(),
            'centroid': cent,
            'snr': snr_val,
            'fwhm': fwhm_val,
            'ew': ew,
            'total': total,
            'maxval': spectrum.flux.max(),
            'minval': spectrum.flux.min()}


@plugin.plugin_bar("Statistics", icon=QIcon(":/icons/012-file.svg"), priority=1)
class StatisticsWidget(QWidget):
    """
    This widget controls the statistics box. It is responsible for calling
    stats computation functions and updating the stats widget. It only takes
    the owner workspace's current data item and selected region for stats
    computations. The stats box can be updated by calling the update_statistics
    function.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_spectrum = None  # Current `Spectrum1D`
        self._current_plot_item = None  # Current plot item
        self.stats = None  # dict with stats

        self._init_ui()

        self.hub.workspace.current_item_changed.connect(self.update_statistics)
        # When the current subwindow changes, update the stat widget
        self.hub.workspace.plot_window_activated.connect(self.update_statistics)
        # When current item changes, update the stat widget
        self.hub.workspace.current_item_changed.connect(self.update_statistics)
        # When selection changes, update the stat widget
        self.hub.workspace.current_selected_changed.connect(self.update_statistics)
        # When new plot window is added, connect signals
        self.hub.workspace.plot_window_added.connect(self._connect_plot_window)
        # When an item in the workspace model changes, update the stat widget
        self.hub.model.itemChanged.connect(self.update_statistics)

        # Connect any currently open plot windows
        for plot_window in self.hub.plot_windows:
            self._connect_plot_window(plot_window)

    def _init_ui(self):
        loadUi(os.path.abspath(
               os.path.join(os.path.dirname(__file__), "statistics.ui")), self)

        # A dict of display `QLineEdit` and their stat keys:
        self.stat_widgets = {
            'mean': self.mean_text_edit,
            'median': self.median_text_edit,
            'stddev': self.std_dev_text_edit,
            'centroid': self.centroid_text_edit,
            'snr': self.snr_text_edit,
            'fwhm': self.fwhm_text_edit,
            'ew': self.eqwidth_text_edit,
            'minval': self.min_val_text_edit,
            'maxval': self.max_val_text_edit,
            'total': self.count_total_text_edit
        }

        self.continuum_subtracted_widgets = [
            self.centroid_text_edit,
            self.centroid_label,
            self.fwhm_text_edit,
            self.fwhm_label
        ]

        self.continuum_normalized_widgets = [
            self.eqwidth_label,
            self.eqwidth_text_edit,
        ]

        # Set ui line height based on the current platform's qfont info
        for widget in self.stat_widgets.values():
            doc = widget.document()
            fm = widget.fontMetrics()
            margins = widget.contentsMargins()
            n_height = (fm.lineSpacing() +
                        (doc.documentMargin() + widget.frameWidth()) * 2 +
                        margins.top() + margins.bottom())
            widget.setFixedHeight(n_height)
        self.comboBox.addItems(["Basic", "Continuum Subtracted", "Continuum Normalized"])
        self.comboBox.currentIndexChanged.connect(self._on_set_statistics_type)
        self._on_set_statistics_type()

    def _connect_plot_window(self, plot_window):
        plot_window.plot_widget.plot_added.connect(self.update_statistics)
        plot_window.plot_widget.plot_removed.connect(self.update_statistics)
        plot_window.plot_widget.roi_moved.connect(self.update_statistics)
        plot_window.plot_widget.roi_removed.connect(self.update_statistics)

    def set_status(self, message):
        self.status_display.setPlainText(message)

    def clear_status(self):
        self.set_status("")

    def _on_set_statistics_type(self, index=0):
        stats_type = self.comboBox.currentText()
        is_subtracted = stats_type == "Continuum Subtracted"
        is_normalized = stats_type == "Continuum Normalized"

        for widget in self.continuum_subtracted_widgets:
            if is_subtracted:
                widget.show()
            else:
                widget.hide()

        for widget in self.continuum_normalized_widgets:
            if is_normalized:
                widget.show()
            else:
                widget.hide()

    def _update_stat_widgets(self, stats):
        """
        Clears all widgets then fills in
        the available stat values.
        Parameters
        ----------
        stats: dict
            Key: key in `StatisticsWidget.stat_widgets`.
            Value: float value to display
        """
        self._clear_stat_widgets()

        if stats is None:
            return
        for key in stats:
            if key in self.stat_widgets:
                text = stats[key] if (stats[key] == "N/A" or stats[key] == "Error") \
                    else format_float_text(stats[key])
                self.stat_widgets[key].document().setPlainText(text)

    def _clear_stat_widgets(self):
        """
        Clears all widgets in `StatisticsWidget.stat_widgets`
        """
        for key in self.stat_widgets:
            self.stat_widgets[key].document().clear()

    @staticmethod
    def pos_to_spectral_region(pos):
        """
        Vet input region position and construct
        a `~specutils.utils.SpectralRegion`.
        Parameters
        ----------
        pos : `~astropy.units.Quantity`
            A tuple `~astropy.units.Quantity` with
            (min, max) range of roi.

        Returns
        -------
        None or `~specutils.utils.SpectralRegion`
        """
        if not isinstance(pos, u.Quantity):
            return None
        elif pos.unit == u.Unit("") or \
                pos[0] == pos[1]:
            return None
        elif pos[0] > pos[1]:
            pos = [pos[1], pos[0]] * pos.unit
        return SpectralRegion(*pos)

    def _get_workspace_region(self):
        """Get current widget region."""
        pos = self.hub.selected_region_bounds

        if pos is not None:
            return self.pos_to_spectral_region(pos)

    def _workspace_has_region(self):
        """True if there is an active region"""
        return self.hub.selected_region is not None

    def _get_target_name(self):
        """Gets name of data and region selected"""
        current_item = self.hub.workspace.current_item
        region = self._get_workspace_region()
        if current_item is not None:
            if isinstance(current_item, PlotDataItem):
                current_item = current_item.data_item
        if current_item is None or not hasattr(current_item, "name"):
            return ""
        if region is None:
            return "Statistics over entire data.\n" \
                   "Data: {0}".format(current_item.name)
        else:
            return "Statistics over single region.\n" \
                   "Data: {0}\n" \
                   "Region Upper: {1:0.5g}\n" \
                   "Region Lower: {2:0.5g}".format(current_item.name,
                                                   region.upper,
                                                   region.lower)

    def clear_statistics(self):
        self._clear_stat_widgets()
        self.stats = None

    def _reconnect_item_signals(self):
        if self.hub.plot_item is self._current_plot_item:
            return

        if isinstance(self._current_plot_item, PlotDataItem):
            self._current_plot_item.spectral_axis_unit_changed.disconnect(self.update_statistics)
            self._current_plot_item.data_unit_changed.disconnect(self.update_statistics)

        self._current_plot_item = self.hub.plot_item

        if isinstance(self._current_plot_item, PlotDataItem):
            self._current_plot_item.spectral_axis_unit_changed.connect(self.update_statistics)
            self._current_plot_item.data_unit_changed.connect(self.update_statistics)

    def _spectrum_with_plot_units(self, spec):
        """
        Make a new spectrum object with the plotted units.

        Returns
        -------
        spectrum : `~specutils.spectra.spectrum1d.Spectrum1D`
        """
        if self._current_plot_item is None:
            return spec

        data_unit = self._current_plot_item.data_unit
        spectral_axis_unit = self._current_plot_item.spectral_axis_unit

        new_spec = spec.new_flux_unit(u.Unit(data_unit))
        new_spec = new_spec.with_spectral_unit(u.Unit(spectral_axis_unit))
        return new_spec

    def update_statistics(self):
        if self.hub.workspace is None or self.hub.plot_item is None:
            return self.clear_statistics()

        # If the plot item is not visible, don't bother updating stats
        if not self.hub.plot_item.visible:
            return self.clear_statistics()

        spec = self.hub.data_item.spectrum if self.hub.data_item is not None else None
        spectral_region = self._get_workspace_region()

        self._current_spectrum = spec
        self._reconnect_item_signals()

        # Check for issues and extract
        # region from input spectra:
        if spec is None:
            self.set_status("No data selected.")
            return self.clear_statistics()
        elif not isinstance(spec, Spectrum1D):
            self.set_status("Spectrum was not found.")
            return self.clear_statistics()
        else:
            spec = self._spectrum_with_plot_units(spec)

        if spectral_region is not None:
            if not check_unit_compatibility(spec, spectral_region):
                self.set_status("Region units are not compatible with "
                                "selected data's spectral axis units.")
                return self.clear_statistics()
            spectral_region = clip_region(spec, spectral_region)
            if spectral_region is None:
                self.set_status("Region out of bound.")
                return self.clear_statistics()
            try:
                idx1, idx2 = spectral_region.bounds
                if idx1 == idx2:
                    self.set_status("Region over single value.")
                    return self.clear_statistics()
                spec = extract_region(spec, spectral_region)
                if not len(spec.flux) > 0:
                    self.set_status("Regione range is too small.")
                    return self.clear_statistics()
            except ValueError as e:
                self.set_status("Region could not be extracted "
                                "from target data.")
                return self.clear_statistics()
        elif self._workspace_has_region():
            self.set_status("Region has no units")
            return self.clear_statistics()

        # Compute stats and update widget:
        self.stats = compute_stats(spec)
        self._update_stat_widgets(self.stats)
        self.set_status(self._get_target_name())

    def update_signal_handler(self, *args, **kwargs):
        """
        Universal signal handler for update calls.
        """
        self.update_statistics()

