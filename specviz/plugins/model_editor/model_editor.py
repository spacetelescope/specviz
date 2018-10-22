import os
import uuid

import numpy as np
from astropy.modeling import models
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QMenu, QMessageBox, QToolButton, QWidget
from qtpy.uic import loadUi
from specutils.fitting import fit_lines
from specutils.spectra import Spectrum1D

from .equation_editor_dialog import ModelEquationEditorDialog
from .items import ModelDataItem
from .models import ModelFittingModel
from ...core.plugin import plugin

MODELS = {
    'Const1D': models.Const1D,
    'Linear1D': models.Linear1D,
    'Gaussian1D': models.Gaussian1D,
}


@plugin.plugin_bar("Model Editor", icon=QIcon(":/icons/012-file.svg"))
class ModelEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "model_editor.ui")), self)

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
            self._on_equation_edit_button_clicked)

        # When a plot data item is select, get its model editor model
        # representation
        self.hub.workspace.current_selected_changed.connect(
            self._on_plot_item_selected)

    @plugin.tool_bar(name="New Model", icon=QIcon(":/icons/012-file.svg"))
    def on_new_model_triggered(self):
        if self.hub.data_item is None:
            message_box = QMessageBox()
            message_box.setText("No item selected, cannot create model.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "There is currently no item selected. Please select an item "
                "before attempting to create a new model.")

            message_box.exec()
            return

        # Set the currently displayed plugin panel widget to the model editor
        self.hub.set_active_plugin_bar(name="Model Editor")

        # Grab the currently selected plot data item
        new_spec = Spectrum1D(flux=np.zeros(self.hub.data_item.spectral_axis.size) * self.hub.data_item.flux.unit,
                              spectral_axis=self.hub.data_item.spectral_axis)

        model_data_item = ModelDataItem(model=ModelFittingModel(),
                                        name="Fittable Model Spectrum",
                                        identifier=uuid.uuid4(),
                                        data=new_spec)

        self.hub.workspace.model.appendRow(model_data_item)

        plot_data_item = self.hub.workspace.proxy_model.item_from_id(
            model_data_item.identifier)

        # Connect data change signals so that the plot updates when the user
        # changes a parameter in the model view model
        model_data_item.model_editor_model.dataChanged.connect(
            lambda tl, br, r, pi=plot_data_item: self._on_model_data_changed(tl, br, pi))

    def _add_fittable_model(self, model):
        idx = self.model_tree_view.model().add_model(model())
        self.model_tree_view.setExpanded(idx, True)

        for i in range(0, 3):
            self.model_tree_view.resizeColumnToContents(i)

    def _on_model_data_changed(self, top_left, bottom_right, plot_data_item):
        if top_left.column() == 1:
            # We only want to update the model if the parameter values
            # are changed, which exist in column 1.
            plot_data_item.set_data()
        elif top_left.column() == 0:
            # In this case, the user has renamed a model. Since the equation
            # editor now doesn't know about the old model, reset the equation
            self.hub.data_item.model_editor_model.reset_equation()

    def _on_equation_edit_button_clicked(self):
        # Get the current model
        model_data_item = self.hub.data_item

        if not isinstance(model_data_item, ModelDataItem):
            message_box = QMessageBox()
            message_box.setText("No model available.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "The currently selected item does not contain a fittable model."
                " Create a new one, or select an item containing a model.")

            message_box.exec()
            return

        equation_editor_dialog = ModelEquationEditorDialog(
            model_data_item.model_editor_model)
        equation_editor_dialog.accepted.connect(self.hub.plot_item.set_data)
        equation_editor_dialog.exec_()

    def _on_plot_item_selected(self, plot_data_item):
        if not isinstance(plot_data_item.data_item, ModelDataItem):
            self.model_tree_view.setModel(None)
            return

        model_data_item = plot_data_item.data_item

        # Set the model on the tree view and expand all children initially.
        self.model_tree_view.setModel(model_data_item.model_editor_model)
        self.model_tree_view.expandAll()

        for i in range(0, 3):
            self.model_tree_view.resizeColumnToContents(i)

    def _on_fit_clicked(self, model_plot_data_item):
        fit_mod = fit_lines(self.hub.data_item.spectrum, result)
        flux = fit_mod(self.hub.data_item.spectrum.spectral_axis)

        new_spec = Spectrum1D(flux=flux,
                              spectral_axis=self.hub.data_item.spectrum.spectral_axis)
        # self.hub.model.add_data(new_spec, "Fitted Model Spectrum")

        # Update the stored plot data item object for this model editor model
        # self._model_editor_model.plot_data_item.data_item.set_data(new_spec)

        # Fitted quantity models do not preserve the names of the sub models
        # which are used to relate the fitted sub models back to the displayed
        # models in the model editor. Go through and hope that their order is
        # preserved.
        if result.n_submodels() > 1:
            for i, x in enumerate(result):
                fit_mod.unitless_model._submodels[i].name = x.name
            sub_mods = [x for x in fit_mod.unitless_model]
        else:
            fit_mod.unitless_model.name = result.name
            sub_mods = [fit_mod.unitless_model]

        disp_mods = {item.text(): item for item in model_editor_model.items}

        for i, sub_mod in enumerate(sub_mods):
            # Get the base astropy model object
            model_item = disp_mods.get(sub_mod.name)

            # For each of the children `StandardItem`s, parse out their
            # individual stored values
            for cidx in range(model_item.rowCount()):
                param_name = model_item.child(cidx, 0).data()

                if result.n_submodels() > 1:
                    parameter = getattr(fit_mod, "{0}_{1}".format(param_name, i))
                else:
                    parameter = getattr(fit_mod, param_name)

                model_item.child(cidx, 1).setText("{:.4g}".format(parameter.value))
                model_item.child(cidx, 1).setData(parameter.value, Qt.UserRole + 1)

                model_item.child(cidx, 3).setData(parameter.fixed, Qt.UserRole + 1)

        for i in range(0, 3):
            self.model_tree_view.resizeColumnToContents(i)