import os
import pickle

import numpy as np
from astropy import units as u
from astropy.modeling import fitting, models
from qtpy.QtWidgets import QMessageBox
from specutils.spectra import Spectrum1D

from specviz.core.hub import Hub


def fill_in_models(model_editor, value_dict):
    """
    Adds model parameters to the model item instance.

    Parameters
    ----------
    model_editor : :class:`specviz.plugins.model_editor.model_editor.ModelEditor`
        The model editor plugin instance.
    value_dict : dict
        Dictionary mapping the name of a model to a dictionary containing
        parameter information.
    """
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


def test_model_fitting(specviz_gui, monkeypatch):
    # Monkeypatch the QMessageBox widget so that it doesn't block the test
    # progression. In this case, accept the information dialog indicating that
    # a loader has been saved.
    monkeypatch.setattr(QMessageBox, "information", lambda *args: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)

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

    index = model_editor.data_selection_combo.findText("fitting_data")
    if index >= 0:
        model_editor.data_selection_combo.setCurrentIndex(index)
    value_dict = {
        'Gaussian1D': {
            'amplitude': '1.3',
            'mean': '0',
            'stddev': '0.1'
        },
        'Gaussian1D1': {
            'amplitude': '1.8',
            'mean': '0.5',
            'stddev': '0.1'
        }
    }
    plot_data_item = hub.plot_item
    model_editor_model = plot_data_item.data_item.model_editor_model

    fill_in_models(model_editor_model, value_dict)

    model_editor._on_fit_clicked(eq_pop_up=False)

    model_editor_model = plot_data_item.data_item.model_editor_model
    result = model_editor_model.evaluate()

    np.testing.assert_allclose(result.parameters, gg_fit.parameters, rtol=1e-4)


def test_save_model(specviz_gui, tmpdir, monkeypatch):
    # Monkeypatch the QMessageBox widget so that it doesn't block the test
    # progression. In this case, accept the information dialog indicating that
    # a loader has been saved.
    monkeypatch.setattr(QMessageBox, "information", lambda *args: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)

    hub = Hub(workspace=specviz_gui.current_workspace)

    model_editor = specviz_gui.current_workspace._plugin_bars['Model Editor']

    # Open the model editor and create a model
    model_editor._on_create_new_model()
    model_editor._add_fittable_model(models.Gaussian1D)

    model_editor_model = hub.plot_item.data_item.model_editor_model
    assert len(model_editor_model.fittable_models) == 1

    outfile = str(tmpdir.join('model.smf'))
    model_editor._save_models(outfile)

    assert os.path.exists(outfile)

    with open(outfile, 'rb') as handle:
        saved_models = pickle.load(handle)

    assert len(saved_models) == 1
    assert 'Gaussian1D' in saved_models
    assert isinstance(saved_models['Gaussian1D'], models.Gaussian1D)


def test_load_model(specviz_gui, tmpdir, monkeypatch):
    # Monkeypatch the QMessageBox widget so that it doesn't block the test
    # progression. In this case, accept the information dialog indicating that
    # a loader has been saved.
    monkeypatch.setattr(QMessageBox, "information", lambda *args: QMessageBox.Ok)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: QMessageBox.Ok)

    hub = Hub(workspace=specviz_gui.current_workspace)

    model_editor = specviz_gui.current_workspace._plugin_bars['Model Editor']

    # Open the model editor
    model_editor._on_create_new_model()
    model_editor_model = hub.plot_item.data_item.model_editor_model

    # Sanity check to make sure no models exist so far
    assert len(model_editor_model.fittable_models) == 0

    # Create a pickle on the fly to use for testing
    model_file = str(tmpdir.join('new_model.smf'))
    new_models = {
        'Gaussian1D': models.Gaussian1D(),
        'Polynomial1D': models.Polynomial1D(degree=4),
        'Linear1D': models.Linear1D()
    }
    with open(model_file, 'wb') as handle:
        pickle.dump(new_models, handle)

    model_editor._load_model_from_file(model_file)
    loaded_models = model_editor_model.fittable_models
    assert len(loaded_models) == len(new_models)
    assert 'Gaussian1D' in loaded_models
    assert isinstance(loaded_models['Gaussian1D'], models.Gaussian1D)
    assert 'Polynomial1D' in loaded_models
    assert isinstance(loaded_models['Polynomial1D'], models.Polynomial1D)
    assert 'Linear1D' in loaded_models
    assert isinstance(loaded_models['Linear1D'], models.Linear1D)
