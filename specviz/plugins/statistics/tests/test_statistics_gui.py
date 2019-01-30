import astropy.units as u
import numpy as np
from astropy.modeling.models import Gaussian1D
from specutils import SpectralRegion, Spectrum1D
from specutils.analysis import centroid, equivalent_width, fwhm, line_flux
from specutils.manipulation import extract_region

from specviz.core.hub import Hub


# todo: we should really add one more test here for stats run on a unit updated plot

def new_workspace(specviz_gui):
    """
    Generate a fresh new workspace for tests that require an unmodified
    workspace instance.

    Parameters
    ----------
    specviz_gui : :class:`~specviz.app.Application`
        The SpecViz application instance.

    Returns
    -------
    workspace : :class:`~specviz.widgets.workspace.Workspace`
        A new workspace instance populated with developer data.
    """
    # Cache a reference to the currently active window
    specviz_gui.current_workspace = specviz_gui.add_workspace()

    # Add an initially empty plot
    specviz_gui.current_workspace.add_plot_window()

    y = Gaussian1D(mean=50, stddev=10)(np.arange(100)) + np.random.sample(
        100) * 0.1

    spec1 = Spectrum1D(flux=y * u.Jy,
                       spectral_axis=np.arange(100) * u.AA)
    spec2 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                       spectral_axis=np.arange(100) * u.Hz)
    spec3 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                       spectral_axis=np.arange(100) * u.Hz)

    data_item = specviz_gui.current_workspace.model.add_data(spec1, "Spectrum 1")
    specviz_gui.current_workspace.model.add_data(spec2, "Spectrum 2")
    specviz_gui.current_workspace.model.add_data(spec3, "Spectrum 3")

    # Set the first item as selected
    specviz_gui.current_workspace.force_plot(data_item)

    return specviz_gui.current_workspace


def test_statistics_gui_full_spectrum(specviz_gui):
    # Ensure that the test is run on an unmodified workspace instance
    workspace = new_workspace(specviz_gui)
    hub = Hub(workspace=workspace)

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

    workspace.close()


def test_statistics_gui_roi_spectrum(specviz_gui):
    # Ensure that the test is run on an unmodified workspace instance
    workspace = new_workspace(specviz_gui)
    hub = Hub(workspace=workspace)

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

    workspace.close()
