import os
import numpy as np

from astropy import units as u

from specutils.spectra.spectral_region import SpectralRegion
from specutils.analysis.snr import snr

from qtpy.QtWidgets import QWidget
from qtpy.uic import loadUi

from ..core.items import PlotDataItem
from ..utils import UI_PATH


def clip_region(spectrum, region):
    if region.lower < spectrum.spectral_axis.min():
        region.lower = spectrum.spectral_axis.min()
    if region.upper > spectrum.spectral_axis.max():
        region.upper = spectrum.spectral_axis.max()
    return region


def compute_stats(spectrum, region=None):
    """
    Compute basic statistics for a spectral region.
    Parameters
    ----------
    spectrum : `~specutils.spectra.spectrum1d.Spectrum1D`
    region: `~specutils.utils.SpectralRegion`
    """

    if region is not None:
        region = clip_region(spectrum, region)
        try:
            spectrum = region.extract(spectrum)
        except ValueError:
            return None

    flux = spectrum.flux

    mean = flux.mean()
    rms = np.sqrt(flux.dot(flux) / len(flux))
    return {'mean': mean,
            'median': np.median(flux),
            'stddev': flux.std(),
            'rms': rms,
            'snr': mean / rms,  # snr(spectrum=spectrum),
            'total': np.trapz(flux)}


def format_text(value):
    v = value
    if isinstance(v, u.Quantity):
        v = value.value
    if 0.001 <= abs(v) <= 1000 or abs(v) == 0.0:
        return "{0:.3f}".format(value)
    else:
        return "{0:.3e}".format(value)


class StatisticsWidget(QWidget):
    def __init__(self, workspace, parent=None):
        super(StatisticsWidget, self).__init__(parent=parent)
        self.workspace = workspace

        self._current_spectrum = None
        self.stats = None

        self._init_ui()

        self.workspace.current_item_changed.connect(self._on_workspace_item_changed)
        self.workspace.list_view.selectionModel().currentChanged.connect(self._on_list_view_changed)

    def _init_ui(self):
        loadUi(os.path.join(UI_PATH, "statistics.ui"), self)

    @property
    def current_spectrum(self):
        return self._current_spectrum

    @property
    def current_workspace_spectrum(self):
        """Sets Data selection to currently active data"""
        current_item = self.workspace.current_item
        if current_item is not None:
            if isinstance(current_item, PlotDataItem):
                current_item = current_item.data_item
        if current_item is not None and hasattr(current_item, "spectrum"):
            return current_item.spectrum
        return None

    @staticmethod
    def pos_to_spectral_region(pos):
        if not isinstance(pos, u.Quantity):
            return None
        elif pos.unit == u.Unit("") or \
                pos[0] == pos[1]:
            return None
        elif pos[0] > pos[1]:
            pos = [pos[1], pos[0]] * pos.unit
        return SpectralRegion(*pos)

    def current_workspace_region(self):
        pos = self.workspace.selected_region_pos
        if pos is not None:
            return self.pos_to_spectral_region(pos)
        return None

    def _on_region_changed(self, pos=None):
        if self.current_spectrum is None:
            self._current_spectrum = self.current_workspace_spectrum

        spec = self.current_spectrum
        if spec is None:
            self.clear_widget_stats()
            return

        spectral_region = self.pos_to_spectral_region(pos)
        stats = compute_stats(spec, spectral_region)
        print(stats)
        self.update_widget_stats(stats)

    def _on_list_view_changed(self, index):
        spec = self.current_workspace_spectrum
        self._current_spectrum = spec

        if spec is None:
            return

        spectral_region = self.current_workspace_region()

        stats = compute_stats(spec, spectral_region)
        print(stats)
        self.update_widget_stats(stats)

    def _on_workspace_item_changed(self, plot_data_item):
        if plot_data_item is None:
            self.clear_widget_stats()
            return

        current_item = plot_data_item.data_item
        if not (current_item is not None) or not hasattr(current_item, "spectrum"):
            return

        spec = current_item.spectrum
        self._current_spectrum = spec

        spectral_region = self.current_workspace_region()

        stats = compute_stats(spec, spectral_region)
        print(stats)
        self.update_widget_stats(stats)

    def update_widget_stats(self, stats):
        if stats is None:
            self.clear_widget_stats()
            return
        self.mean_line_edit.setText(format_text(stats['mean']))
        self.median_line_edit.setText(format_text(stats['median']))
        self.std_dev_line_edit.setText(format_text(stats['stddev']))
        self.rms_line_edit.setText(format_text(stats['rms']))
        self.snr_line_edit.setText(format_text(stats['snr']))
        self.count_total_line_edit.setText(format_text(stats['total']))
        self.stats = stats

    def clear_widget_stats(self):
        self.mean_line_edit.setText("")
        self.median_line_edit.setText("")
        self.std_dev_line_edit.setText("")
        self.rms_line_edit.setText("")
        self.snr_line_edit.setText("")
        self.count_total_line_edit.setText("")
        self.stats = None





