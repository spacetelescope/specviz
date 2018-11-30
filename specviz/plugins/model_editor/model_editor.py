import os
import pickle
import uuid

import numpy as np
from astropy.modeling import fitting, models, optimizers
from qtpy.QtCore import Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (QAction, QDialog, QFileDialog, QInputDialog, QMenu,
                            QMessageBox, QToolButton, QWidget)
from qtpy.uic import loadUi
from specutils.fitting import fit_lines
from specutils.manipulation import extract_region
from specutils.spectra import Spectrum1D

from .equation_editor_dialog import ModelEquationEditorDialog
from .initializers import initialize
from .items import ModelDataItem
from .models import ModelFittingModel
from ...core.plugin import plugin

MODELS = {
    'Const1D': models.Const1D,
    'Linear1D': models.Linear1D,
    'Polynomial1D': models.Polynomial1D,
    'Gaussian1D': models.Gaussian1D,
    'Voigt1D': models.Voigt1D,
    'Lorentzian1D': models.Lorentz1D,
}

FITTERS = {
    'Levenberg-Marquardt': fitting.LevMarLSQFitter,
    'Simplex Least Squares': fitting.SimplexLSQFitter,
    # Disabled # 'SLSQP Optimization': fitting.SLSQPLSQFitter,
}

SPECVIZ_MODEL_FILE_FILTER = 'Specviz Model Files (*.smf)'


@plugin.plugin_bar("Model Editor", icon=QIcon(":/icons/012-file.svg"))
class ModelEditor(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fitting_options = {
            'fitter': 'Levenberg-Marquardt',
            'displayed_digits': 5,
            'max_iterations': optimizers.DEFAULT_MAXITER,
            'relative_error': optimizers.DEFAULT_ACC,
            'epsilon': optimizers.DEFAULT_EPS,
        }

        self._init_ui()

    def _init_ui(self):
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

        # Initially hide the model editor tools until user has selected an
        # editable model spectrum object
        self.editor_holder_widget.setHidden(True)
        self.setup_holder_widget.setHidden(False)

        self.equation_edit_button.clicked.connect(
            self._on_equation_edit_button_clicked)
        self.new_model_button.clicked.connect(self._on_create_new_model)
        self.remove_model_button.clicked.connect(self._on_remove_model)

        self.advanced_settings_button.clicked.connect(
            lambda: ModelAdvancedSettingsDialog(self, self).exec())

        self.save_model_button.clicked.connect(self._on_save_model)
        self.load_model_button.clicked.connect(self._on_load_from_file)

        self.data_selection_combo.setModel(self.hub.model)
        self.data_selection_combo.currentIndexChanged.connect(self._redraw_model)

        # When a plot data item is select, get its model editor model
        # representation
        self.hub.workspace.current_selected_changed.connect(
            self._on_plot_item_selected)

        # When the plot window changes, reset model editor
        self.hub.workspace.mdi_area.subWindowActivated.connect(self._on_new_plot_activated)

        # Listen for when data items are added to internal model
        self.hub.model.data_added.connect(self._on_data_item_added)

        # Connect the fit model button
        self.fit_button.clicked.connect(self._on_fit_clicked)

    def new_message_box(self, text, info=None, icon=QMessageBox.Warning):
        message_box = QMessageBox()
        message_box.setText(text)
        message_box.setIcon(icon)
        if info is not None:
            message_box.setInformativeText(info)
        message_box.exec()
        return

    @plugin.tool_bar(name="New Model", icon=QIcon(":/icons/012-file.svg"))
    def on_new_model_triggered(self):
        self._on_create_new_model()

    def _on_data_item_added(self, data_item):
        if not isinstance(data_item, ModelDataItem):
            return

        model_data_item = data_item
        plot_data_item = self.hub.plot_data_item_from_data_item(model_data_item)

        # Connect data change signals so that the plot updates when the user
        # changes a parameter in the model view model
        model_data_item.model_editor_model.itemChanged.connect(
            lambda item: self._on_model_item_changed(item))

        # plot_data_item = self.hub.workspace.proxy_model.item_from_id(model_data_item.identifier)
        plot_data_item.visible = True

        self.hub.workspace.current_plot_window.plot_widget.on_item_changed(
            model_data_item)
        self.hub.workspace._on_item_changed(item=plot_data_item.data_item)

    def _on_create_new_model(self):
        if self.hub.data_item is None:
            self.new_message_box(text="No item selected, cannot create model.",
                                 info="There is currently no item selected. "
                                      "Please select an item before attempting"
                                      " to create a new model.")

        # Grab the currently selected plot data item
        new_spec = Spectrum1D(flux=np.zeros(self.hub.data_item.spectral_axis.size) * self.hub.data_item.flux.unit,
                              spectral_axis=self.hub.data_item.spectral_axis)

        self.create_model_data_item(new_spec, data_item=self.hub.data_item)

    def create_model_data_item(self, spectrum, name=None, data_item=None):
        """
        Generate a new model data item to be added to the data list.

        Parameters
        ----------
        spectrum : :class:`~specutils.Spectrum1D`
            The spectrum holding the spectral data.
        """
        # Set the currently displayed plugin panel widget to the model editor
        self.hub.set_active_plugin_bar(name="Model Editor")

        model_data_item = ModelDataItem(model=ModelFittingModel(),
                                        name=name or "Fittable Model Spectrum",
                                        identifier=uuid.uuid4(),
                                        data=spectrum)
        model_data_item._selected_data = data_item

        self.hub.append_data_item(model_data_item)

        if model_data_item._selected_data is not None:
            index = self.data_selection_combo.findData(model_data_item._selected_data)
            if index != -1:
                self.data_selection_combo.setCurrentIndex(index)

    def _on_remove_model(self):
        """Remove an astropy model from the model editor tree view."""
        indexes = self.model_tree_view.selectionModel().selectedIndexes()

        if len(indexes) > 0:
            selected_idx = indexes[0]
            self.model_tree_view.model().remove_model(row=selected_idx.row())

            # If removing the model resulted in an invalid arithmetic equation,
            # force open the arithmetic editor so the user can fix it.
            if self.model_tree_view.model().equation and self.model_tree_view.model().evaluate() is None:
                self._on_equation_edit_button_clicked()

    def _save_models(self, filename):
        model_editor_model = self.hub.plot_item.data_item.model_editor_model
        models = model_editor_model.fittable_models

        with open(filename, 'wb') as handle:
            pickle.dump(models, handle)

    def _on_save_model(self, interactive=True):
        model_editor_model = self.hub.data_item.model_editor_model
        # There are no models to save
        if not model_editor_model.fittable_models:
            self.new_message_box(text='No model available',
                                 info='No model exists to be saved.')
            return

        default_name = os.path.join(os.path.curdir, 'new_model.smf')
        outfile = QFileDialog.getSaveFileName(
            self, caption='Save Model', directory=default_name,
            filter=SPECVIZ_MODEL_FILE_FILTER)[0]
        # No file was selected; the user hit "Cancel"
        if not outfile:
            return

        self._save_models(outfile)

        self.new_message_box(
            text='Model saved',
            info='Model successfully saved to {}'.format(outfile),
            icon=QMessageBox.Information)

    def _load_model_from_file(self, filename):
        with open(filename, 'rb') as handle:
            loaded_models = pickle.load(handle)

        for _, model in loaded_models.items():
            self._add_model(model)

    def _on_load_from_file(self):
        filename = QFileDialog.getOpenFileName(
            self, caption='Load Model',
            filter=SPECVIZ_MODEL_FILE_FILTER)[0]
        if not filename:
            return

        self._load_model_from_file(filename)

    def _add_model(self, model):
        idx = self.model_tree_view.model().add_model(model)
        self.model_tree_view.setExpanded(idx, True)

        for i in range(0, 4):
            self.model_tree_view.resizeColumnToContents(i)

        self._redraw_model()

    def _add_fittable_model(self, model_type):
        if issubclass(model_type, models.Polynomial1D):
            text, ok = QInputDialog.getInt(self, 'Polynomial1D',
                                           'Enter Polynomial1D degree:')
            # User decided not to create a model after all
            if not ok:
                return

            model = model_type(int(text))
        else:
            model = model_type()

        # Grab any user-defined regions so we may initialize parameters only
        # for the selected data.
        inc_regs = self.hub.spectral_regions
        spec = self._get_selected_plot_data_item().data_item.spectrum

        if inc_regs is not None:
            spec = extract_region(spec, inc_regs)

        # Initialize the parameters
        model = initialize(model, spec.spectral_axis, spec.flux)

        self._add_model(model)

    def _update_model_data_item(self):
        """
        When a new data item is selected, check if
        the model's plot_data_item units are compatible
        with the target data item's plot_data_item units.
        If the units are not the same, update the model's units.
        """
        # Note
        # ----
        # Target data items that cannot be plotted are not
        # selectable in the data selection combo. The only instance
        # a unit change is needed is when noting is plotted and the
        # user changes the target data.

        # Get the current plot item and update
        # its data item if its a model plot item
        model_plot_data_item = self.hub.plot_item

        if model_plot_data_item is not None and \
                isinstance(model_plot_data_item.data_item, ModelDataItem):
            # This is the data item selected in the
            # model editor data selection combo box
            data_item = self._get_selected_data_item()

            if data_item is not None and \
                    isinstance(data_item.spectrum, Spectrum1D):

                selected_plot_data_item = self.hub.plot_data_item_from_data_item(data_item)

                new_spectral_axis_unit = selected_plot_data_item.spectral_axis_unit
                new_data_unit = selected_plot_data_item.data_unit

                compatible = model_plot_data_item.are_units_compatible(
                    new_spectral_axis_unit,
                    new_data_unit,
                )
                if not compatible:
                    # If not compatible, update the units of every
                    # model plot_data_item unit to match the selected
                    # data's plot_data_item units in every plot sub-window
                    model_identifier = model_plot_data_item.data_item.identifier
                    selection_identifier = selected_plot_data_item.data_item.identifier
                    for sub_window in self.hub.workspace.mdi_area.subWindowList():
                        proxy_model = sub_window.proxy_model

                        # Get plot_data_items in that sub_window
                        model_p_d_i = proxy_model.item_from_id(model_identifier)
                        selected_p_d_i = proxy_model.item_from_id(selection_identifier)

                        # Update model's plot_data_item units
                        model_p_d_i._spectral_axis_unit = selected_p_d_i.spectral_axis_unit
                        model_p_d_i._data_unit = selected_p_d_i.data_unit
                        sub_window.plot_widget.check_plot_compatibility()

                # Copy the spectrum and assign the current
                # fittable model the spectrum with the
                # spectral axis and flux converted to plot units.
                spectrum = data_item.spectrum.with_spectral_unit(new_spectral_axis_unit)
                spectrum = spectrum.new_flux_unit(new_data_unit)
                model_plot_data_item.data_item.set_data(spectrum)
                model_plot_data_item.data_item._selected_data = data_item

    def _redraw_model(self):
        """
        Re-plot the current model item.
        """
        model_plot_data_item = self.hub.plot_item

        if model_plot_data_item is not None and \
                isinstance(model_plot_data_item.data_item, ModelDataItem):
            self._update_model_data_item()
            model_plot_data_item.set_data()

    def _on_model_item_changed(self, item):
        if item.parent():
            # If the item has a parent, then we know that the parameter
            # value has changed. Note that the internal stored data has not
            # been truncated at all, only the displayed text value. All fitting
            # uses the full, un-truncated data value.
            if item.column() == 1:
                item.setData(float(item.text()), Qt.UserRole + 1)
                item.setText(item.text())
            self._redraw_model()
        else:
            # In this case, the user has renamed a model. Since the equation
            # editor now doesn't know about the old model, reset the equation
            self.hub.data_item.model_editor_model.reset_equation()

    def _on_equation_edit_button_clicked(self):
        # Get the current model
        model_data_item = self.hub.data_item

        if not isinstance(model_data_item, ModelDataItem):
            self.new_message_box(text="No model available.",
                                 info="The currently selected item does not"
                                      " contain a fittable model. Create a new"
                                      " one, or select an item containing a model.")
            return

        equation_editor_dialog = ModelEquationEditorDialog(
            model_data_item.model_editor_model)
        equation_editor_dialog.accepted.connect(self.hub.plot_item.set_data)
        equation_editor_dialog.exec_()

    def _clear_tree_view(self):
        self.model_tree_view.setModel(None)
        self.editor_holder_widget.setHidden(True)
        self.setup_holder_widget.setHidden(False)

    def _on_new_plot_activated(self):
        plot_data_item = self.hub.plot_item
        if plot_data_item is not None:
            if isinstance(plot_data_item.data_item, ModelDataItem):
                return self._on_plot_item_selected(plot_data_item)
        self._clear_tree_view()

    def _on_plot_item_selected(self, plot_data_item):
        if not isinstance(plot_data_item.data_item, ModelDataItem):
            return self._clear_tree_view()

        self.editor_holder_widget.setHidden(False)
        self.setup_holder_widget.setHidden(True)

        model_data_item = plot_data_item.data_item

        # Set the model on the tree view and expand all children initially.
        self.model_tree_view.setModel(model_data_item.model_editor_model)
        self.model_tree_view.expandAll()
        if model_data_item._selected_data is not None:
            index = self.data_selection_combo.findData(model_data_item._selected_data)
            if index != -1:
                self.data_selection_combo.setCurrentIndex(index)

        for i in range(0, 4):
            self.model_tree_view.resizeColumnToContents(i)

    def _get_selected_plot_data_item(self):
        workspace = self.hub.workspace

        if self.hub.proxy_model is None:
            raise Exception("Workspace proxy_model is None")

        row = self.data_selection_combo.currentIndex()
        idx = workspace.list_view.model().index(row, 0)

        return self.hub.proxy_model.data(idx, role=Qt.UserRole)

    def _get_selected_data_item(self):
        # The spectrum_data_item would be the data item that this model is to
        # be fit to. This selection is done via the data_selection_combo.
        combo_index = self.data_selection_combo.currentIndex()
        data_item = self.data_selection_combo.itemData(combo_index)

        # If user chooses a model instead of a data item, notify and return
        if isinstance(data_item, ModelDataItem):
            self.new_message_box(text="Selected data is a model.",
                                 info="The currently selected data "
                                      "is a model. Please select a "
                                      "data item containing spectra.")
            return None
        return data_item

    def _on_fit_clicked(self, eq_pop_up=True):
        if eq_pop_up:
            self._on_equation_edit_button_clicked()

        # Grab the currently selected plot data item from the data list
        plot_data_item = self.hub.plot_item

        # If this item is not a model data item, bail
        if not isinstance(plot_data_item.data_item, ModelDataItem):
            return

        data_item = self._get_selected_data_item()

        if data_item is None:
            return

        spectral_region = self.hub.spectral_regions

        # Compose the compound model from the model editor sub model tree view
        model_editor_model = plot_data_item.data_item.model_editor_model
        result = model_editor_model.evaluate()

        if result is None:
            return self.new_message_box(text="Please add models to fit.",
                                        info="Models can be added by clicking the"
                                             " green \"add\" button and selecting a"
                                             " model from the drop-down menu")

        # Load options
        fitter = FITTERS[self.fitting_options["fitter"]]
        output_formatter = "{:0.%sg}" % self.fitting_options['displayed_digits']

        kwargs = {}
        if fitter is fitting.LevMarLSQFitter:
            kwargs['maxiter'] = self.fitting_options['max_iterations']
            kwargs['acc'] = self.fitting_options['relative_error']
            kwargs['epsilon'] = self.fitting_options['epsilon']

        # Run the compound model through the specutils fitting routine. Ensure
        # that the returned values are always in units of the current plot by
        # passing in the spectrum with the spectral axis and flux
        # converted to plot units.
        spectrum = data_item.spectrum.with_spectral_unit(
            plot_data_item.spectral_axis_unit)
        spectrum = spectrum.new_flux_unit(plot_data_item.data_unit)

        fit_mod = fit_lines(spectrum, result, fitter=fitter(),
                            window=spectral_region, **kwargs)

        if fit_mod is None:
            return

        # Fitted quantity models do not preserve the names of the sub models
        # which are used to relate the fitted sub models back to the displayed
        # models in the model editor. Go through and hope that their order is
        # preserved.

        """
        # Uncomment for when specutils function is working with units
        if result.n_submodels() > 1:
            for i, x in enumerate(result):
                fit_mod.unitless_model._submodels[i].name = x.name
            sub_mods = [x for x in fit_mod.unitless_model]
        else:
            fit_mod.unitless_model.name = result.name
            sub_mods = [fit_mod.unitless_model]
        """

        if result.n_submodels() > 1:
            sub_mods = [x for x in fit_mod._submodels]
            for i, x in enumerate(result):
                fit_mod._submodels[i].name = x.name
        else:
            fit_mod.name = result.name
            sub_mods = [fit_mod]

        # Get a list of the displayed name for each sub model in the tree view
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

                model_item.child(cidx, 1).setText(output_formatter.format(parameter.value))
                model_item.child(cidx, 1).setData(parameter.value, Qt.UserRole + 1)
                model_item.child(cidx, 3).setData(parameter.fixed, Qt.UserRole + 1)

        for i in range(0, 4):
            self.model_tree_view.resizeColumnToContents(i)

        # Update the displayed data on the plot
        self._redraw_model()


class ModelAdvancedSettingsDialog(QDialog):
    def __init__(self, model_editor, parent=None):
        super().__init__(parent)

        self.model_editor = model_editor
        self._init_ui()

    def _init_ui(self):
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".",
                         "model_advanced_settings.ui")), self)

        self.fitting_type_combo_box.addItems(list(FITTERS.keys()))

        self.buttonBox.accepted.connect(self.apply_settings)
        self.buttonBox.rejected.connect(self.cancel)

        fitting_options = self.model_editor.fitting_options

        self.displayed_digits_spin_box.setValue(fitting_options['displayed_digits'])
        self.max_iterations_line_edit.setText(str(fitting_options['max_iterations']))
        self.relative_error_line_edit.setText(str(fitting_options['relative_error']))
        self.epsilon_line_edit.setText(str(fitting_options['epsilon']))
        self.fitting_type_combo_box.currentIndexChanged.connect(self._on_index_change)
        index = self.fitting_type_combo_box.findText(fitting_options['fitter'],
                                                     Qt.MatchFixedString)
        if index >= 0:
            self.fitting_type_combo_box.setCurrentIndex(index)

        self._on_index_change()

    def _on_index_change(self, *args):
        fitting_type = self.fitting_type_combo_box.currentText()
        is_lev_mar_lsq = fitting_type == 'Levenberg-Marquardt'
        self.max_iterations_line_edit.setDisabled(not is_lev_mar_lsq)
        self.relative_error_line_edit.setDisabled(not is_lev_mar_lsq)
        self.epsilon_line_edit.setDisabled(not is_lev_mar_lsq)

    def _validate_inputs(self):
        """
        Check if user inputs are valid.
        return
        ------
        success : bool
            True if all input boxes are valid.
        """
        red = "background-color: rgba(255, 0, 0, 128);"
        success = True

        for widget in [self.max_iterations_line_edit]:
            try:
                int(widget.text())
                widget.setStyleSheet("")
            except ValueError:
                widget.setStyleSheet(red)
                success = False

        for widget in [self.relative_error_line_edit,
                       self.epsilon_line_edit]:
            try:
                float(widget.text())
                widget.setStyleSheet("")
            except ValueError:
                widget.setStyleSheet(red)
                success = False

        return success

    def apply_settings(self):
        if not self._validate_inputs():
            return

        fitting_type = self.fitting_type_combo_box.currentText()
        max_iterations = int(self.max_iterations_line_edit.text())
        relative_error = float(self.relative_error_line_edit.text())
        epsilon = float(self.epsilon_line_edit.text())
        displayed_digits = self.displayed_digits_spin_box.value()

        self.model_editor.fitting_options = {
            'fitter': fitting_type,
            'displayed_digits': displayed_digits,
            'max_iterations': max_iterations,
            'relative_error': relative_error,
            'epsilon': epsilon,
        }

        self.close()

    def cancel(self):
        self.close()
