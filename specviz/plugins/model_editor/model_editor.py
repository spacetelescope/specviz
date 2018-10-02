import os

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget, QMessageBox, QToolButton, QMenu, QAction
from qtpy.uic import loadUi
from qtpy.QtCore import Qt

from .equation_editor_dialog import ModelEquationEditorDialog
from .models import ModelFittingModel
from ...core.plugin import Plugin, plugin_bar

from specutils.spectra import Spectrum1D
from specutils.fitting import fit_lines

from astropy.modeling import models
import astropy.units as u


MODELS = {
    'Const1D': models.Const1D,
    'Linear1D': models.Linear1D,
    'Gaussian1D': models.Gaussian1D,
}


@plugin_bar("Model Editor", icon=QIcon(":/icons/012-file.svg"))
class ModelEditor(QWidget, Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "model_editor.ui")), self)

        # Instantiate the model fitting model
        self._model_editor_model = ModelFittingModel()

        # Set the model on the tree view and expand all children initially.
        self.model_tree_view.setModel(self._model_editor_model)
        self.model_tree_view.expandAll()

        # Store a reference to the equation editor dialog. This way, after a
        # user has closed the dialog, the state of the text edit box will be
        # preserved.
        self._equation_dialog = ModelEquationEditorDialog(
                self._model_editor_model)

        # Populate the add mode button with a dropdown containing available
        # fittable model objects
        self.add_model_button.setPopupMode(QToolButton.InstantPopup)
        models_menu = QMenu(self.add_model_button)
        self.add_model_button.setMenu(models_menu)

        for k, v in MODELS.items():
            action = QAction(k, models_menu)
            action.triggered.connect(lambda x, m=v: self._add_fittable_model(m))
            models_menu.addAction(action)

        self.equation_edit_button.clicked.connect(
            self._equation_dialog.exec_)

        # When the equation editor dialog input is accepted, create the
        self._equation_dialog.accepted.connect(
            lambda: self._on_equation_accepted(self._equation_dialog.result))

        for i in range(1, 4):
            self.model_tree_view.resizeColumnToContents(i)

    def _on_equation_accepted(self, result):
        if self.data_item is None:
            message_box = QMessageBox()
            message_box.setText("No item selected, cannot fit model.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "There is currently no item selected. Please select an item "
                "before attempting to fit the model.")

            message_box.exec()
            return

        # Create a new spectrum1d object and add it to the view
        fit_mod = fit_lines(self.data_item.spectrum, result)
        new_spec = Spectrum1D(flux=fit_mod(self.data_item.spectrum.spectral_axis),
                              spectral_axis=self.data_item.spectrum.spectral_axis)
        self.model.add_data(new_spec, "Fitted Model Spectrum")
        self.plot_widget.autoRange()

        # Fitted quantity models do not preserve the names of the sub models
        # which are used to relate the fitted sub models back to the displayed
        # models in the model editor. Go through and hope that their order is
        # preserved.
        if result.n_submodels() > 1:
            for i, x in enumerate(result):
                fit_mod.unitless_model[i].name = x.name
        else:
            fit_mod.unitless_model.name = result.name

        # At this point, the results are valid and accepted. Now, update
        # the displayed values in the model editor
        if fit_mod.unitless_model.n_submodels() > 1:
            sub_mods = [x for x in fit_mod.unitless_model]
        else:
            sub_mods = [fit_mod.unitless_model]

        disp_mods = {self._model_editor_model.item(idx).text(): self._model_editor_model.item(idx)
                     for idx in range(self._model_editor_model.rowCount())}

        for sub_mod in sub_mods:
            # Get the base astropy model object
            model_item = disp_mods.get(sub_mod.name)

            # For each of the children `StandardItem`s, parse out their
            # individual stored values
            for cidx in range(model_item.rowCount()):
                param_name = model_item.child(cidx, 0).data()
                parameter = getattr(sub_mod, param_name)

                model_item.child(cidx, 1).setText("{:.4g}".format(parameter.value))
                model_item.child(cidx, 1).setData(parameter.value, Qt.UserRole + 1)

                model_item.child(cidx, 3).setData(parameter.fixed, Qt.UserRole + 1)

        for i in range(1, 4):
            self.model_tree_view.resizeColumnToContents(i)

    def _add_fittable_model(self, model):
        idx = self._model_editor_model.add_model(model())
        self.model_tree_view.setExpanded(idx, True)

        for i in range(1, 4):
            self.model_tree_view.resizeColumnToContents(i)
