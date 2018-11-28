import numpy as np

from specutils import SpectralRegion
from specutils.analysis import equivalent_width, fwhm, centroid, line_flux
from specutils.manipulation import extract_region

from specviz.core.hub import Hub

# todo: we should really add one more test here for stats run on a unit updated plot


def test_statistics_gui_full_spectrum(specviz_gui):

    hub = Hub(workspace=specviz_gui.current_workspace)

    # pull out stats dictionary
    stats_dict = specviz_gui.current_workspace._plugin_bars['Statistics'].stats

    # Generate truth comparisons
    spectrum = hub.plot_item._data_item.spectrum
    truth_dict = {'mean': spectrum.flux.mean(),
                  'median': np.median(spectrum.flux),
                  'stddev': spectrum.flux.std(),
                  'centroid': centroid(spectrum, region=None),
                  'snr': "N/A",
                  'fwhm': fwhm(spectrum),
                  'ew': equivalent_width(spectrum),
                  'total': line_flux(spectrum),
                  'maxval': spectrum.flux.max(),
                  'minval': spectrum.flux.min()}

    # compare!
    assert stats_dict == truth_dict


def test_statistics_gui_roi_spectrum(specviz_gui):

    hub = Hub(workspace=specviz_gui.current_workspace)

    # Make region of interest cutout, using default cutout at .3 from the
    # middle in either direction
    specviz_gui.current_workspace.current_plot_window.plot_widget._on_add_linear_region()

    # Simulate cutout for truth data
    spectrum = extract_region(hub.plot_item._data_item.spectrum,
                              SpectralRegion(*hub.selected_region_bounds))

    # pull out stats dictionary
    stats_dict = specviz_gui.current_workspace._plugin_bars['Statistics'].stats

    # Generate truth comparisons
    truth_dict = {'mean': spectrum.flux.mean(),
                  'median': np.median(spectrum.flux),
                  'stddev': spectrum.flux.std(),
                  'centroid': centroid(spectrum, region=None),
                  'snr': "N/A",
                  'fwhm': fwhm(spectrum),
                  'ew': equivalent_width(spectrum),
                  'total': line_flux(spectrum),
                  'maxval': spectrum.flux.max(),
                  'minval': spectrum.flux.min()}

    # compare!
    assert stats_dict == truth_dict
