import numpy as np

from astropy import units as u
from astropy.modeling import models, fitting

from specutils.spectra import Spectrum1D

from specutils import SpectralRegion
from specutils.analysis import equivalent_width, fwhm, centroid, line_flux
from specutils.manipulation import extract_region

from specviz.core.hub import Hub

from time import sleep
def fill_in_models(model_editor, value_dict):
    for model_item in model_editor.items:
        name = model_item.text()
        if name not in value_dict.keys():
            continue
        values = value_dict[name]
        # For each of the children `StandardItem`s, parse out their
        # individual stored values
        for cidx in range(model_item.rowCount()):
            param_name = model_item.child(cidx, 0).data()
            model_item.child(cidx, 1).setText(values[param_name])


def test_model_fitting(specviz_gui):
    hub = Hub(workspace=specviz_gui.current_workspace)

    # Generate fake data
    np.random.seed(42)
    g1 = models.Gaussian1D(1, 0, 0.2)
    g2 = models.Gaussian1D(2.5, 0.5, 0.1)

    x = np.linspace(-1, 1, 200)
    y = g1(x) + g2(x) + np.random.normal(0., 0.2, x.shape)

    # Regular fitting
    gg_init = models.Gaussian1D(1.3, 0, 0.1) + models.Gaussian1D(1.8, 0.5, 0.1)
    fitter = fitting.LevMarLSQFitter()
    gg_fit = fitter(gg_init, x, y)


    # SpecViz fitting
    spectral_axis_unit = u.Unit(hub.plot_window.plot_widget.spectral_axis_unit or "")
    data_units = u.Unit(hub.plot_window.plot_widget.data_unit or "")
    s1d = Spectrum1D(flux=y * data_units,
                     spectral_axis=x * spectral_axis_unit)
    hub.workspace.model.add_data(s1d, name="fitting_data")
model_editor = specviz_gui.current_workspace._plugin_bars['Model Editor']

model_editor._on_create_new_model()
model_editor._add_fittable_model(models.Gaussian1D)
model_editor._add_fittable_model(models.Gaussian1D)

    # value_dict = {
    #     'Gaussian1D': {
    #         'amplitude': '1.3',
    #         'mean': '0',
    #         'stddev': '0.1'
    #     },
    #     'Gaussian1D1': {
    #         'amplitude': '1.8',
    #         'mean': '0.5',
    #         'stddev': '0.1'
    #     }
    # }
    #
    # fill_in_models(model_editor, value_dict)
    sleep(10)


def statistics_gui_full_spectrum(specviz_gui):
    hub = Hub(workspace=specviz_gui.current_workspace)
    # Make sure that there are only 3 data items currently
    assert len(hub.data_items) == 3

    # pull out stats dictionary
    stats_dict = specviz_gui.current_workspace._plugin_bars['Statistics'].stats

    # Generate truth comparisons
    spectrum = hub.plot_item._data_item.spectrum
    truth_dict = {'mean': spectrum.flux.mean(),
                  'median': np.median(spectrum.flux),
                  'stddev': spectrum.flux.std(),
                  'centroid': centroid(spectrum, region=None),
                  'rms': np.sqrt(spectrum.flux.dot(spectrum.flux) / len(spectrum.flux)),
                  'snr': "N/A",
                  'fwhm': fwhm(spectrum),
                  'ew': equivalent_width(spectrum),
                  'total': line_flux(spectrum),
                  'maxval': spectrum.flux.max(),
                  'minval': spectrum.flux.min()}

    # compare!
    assert stats_dict == truth_dict


def statistics_gui_roi_spectrum(specviz_gui):

    hub = Hub(workspace=specviz_gui.current_workspace)
    # Make sure that there are only 3 data items currently
    assert len(hub.data_items) == 3

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
                  'rms': np.sqrt(
                      spectrum.flux.dot(spectrum.flux) / len(spectrum.flux)),
                  'snr': "N/A",
                  'fwhm': fwhm(spectrum),
                  'ew': equivalent_width(spectrum),
                  'total': line_flux(spectrum),
                  'maxval': spectrum.flux.max(),
                  'minval': spectrum.flux.min()}

    # compare!
    assert stats_dict == truth_dict