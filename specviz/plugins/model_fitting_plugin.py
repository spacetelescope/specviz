"""
Plugin enabling model definition and fitting
"""
import logging
import os
import re

import numpy as np
from qtpy import compat
from qtpy.QtCore import Qt
# from qtpy.QtGui import
from qtpy.QtWidgets import QTreeWidgetItem
from qtpy.QtGui import QIntValidator, QDoubleValidator
from qtpy.uic import loadUi

from ..core.events import dispatch
from ..core.data import Spectrum1DRefModelLayer
from ..core.threads import FitModelThread
from ..interfaces.factories import ModelFactory, FitterFactory
from ..interfaces.initializers import initialize
from ..interfaces.model_io import yaml_model_io, py_model_io
from ..widgets.plugin import Plugin
from ..widgets.utils import UI_PATH

# To memorize last visited directory.
_model_directory = os.path.expanduser('~')


class ModelFittingPlugin(Plugin):
    """
    UI plugin for model definition, fitting, and management
    """
    name = "Model Fitting"
    location = "right"

    def __init__(self, *args, **kwargs):
        super(ModelFittingPlugin, self).__init__(*args, **kwargs)
        self.fit_model_thread = FitModelThread()

        self.fit_model_thread.status.connect(
            dispatch.on_status_message.emit)

        self.fit_model_thread.result.connect(
            lambda layer: dispatch.on_update_model.emit(layer=layer))

        self.contents.tree_widget_current_models.setColumnWidth(2, 50)

    def setup_ui(self):
        loadUi(os.path.join(UI_PATH, "model_fitting_plugin.ui"), self.contents)

        # Hide the advanced settings initially
        self.contents.group_box_advanced_settings.hide()

        # Create validators advanced settings inputs
        max_iter_valid = QIntValidator(1, 9999, self)
        self.contents.max_iterations_line_edit.setValidator(max_iter_valid)

        rel_err_valid = QDoubleValidator(0, 9999.0, 20, self)
        self.contents.relative_error_line_edit.setValidator(rel_err_valid)

        eps_valid = QDoubleValidator(0, 9999.0, 20, self)
        self.contents.epsilon_line_edit.setValidator(eps_valid)

    def setup_connections(self):
        # Enable/disable buttons depending on selection
        self.contents.tree_widget_current_models.itemSelectionChanged.connect(
            self.toggle_buttons)

        # # Populate model dropdown
        self.contents.combo_box_models.addItems(
            sorted(ModelFactory.all_models))

        # Populate fitting algorithm dropdown
        self.contents.combo_box_fitting.addItems(
            sorted(FitterFactory.all_fitters))

        # When the add new model button is clicked, create a new model
        self.contents.button_select_model.clicked.connect(
            self.add_model)

        # When the model items in the model tree change
        self.contents.tree_widget_current_models.itemChanged.connect(
            self._model_parameter_validation)

        # When the model parameters in the model tree are locked/unlocked
        self.contents.tree_widget_current_models.itemClicked.connect(
            self._fix_model_parameter
        )

        # When the model list delete button is pressed
        self.contents.button_remove_model.clicked.connect(
            lambda: self.remove_model_item())

        self.contents.button_remove_model.clicked.connect(
            self.toggle_buttons)

        # When editing the formula is finished, send event
        self.contents.line_edit_model_arithmetic.editingFinished.connect(
            lambda: self.update_model_formula())

        # Attach the fit button
        self.contents.button_perform_fit.clicked.connect(
            self.fit_model_layer)

        # Update model name when a user makes changes
        self.contents.tree_widget_current_models.itemChanged.connect(self._update_model_name)

        # ---
        # IO
        # Attach the model save/read buttons
        self.contents.button_save_model.clicked.connect(
            self.save_model)

        self.contents.button_load_model.clicked.connect(
            lambda: self.load_model())

        self.contents.button_export_model.clicked.connect(
            self.export_model)

        self.contents.check_box_advanced_settings.clicked.connect(
            lambda state: self.contents.group_box_advanced_settings.setHidden(not state)
        )

    @property
    def current_model(self):
        model_item = self.current_model_item
        model = model_item.data(0, Qt.UserRole)

        return model

    @property
    def current_model_item(self):
        return self.contents.tree_widget_current_models.currentItem()

    def add_model(self):
        layer = self.current_layer

        if layer is None:
            return

        model_name = self.contents.combo_box_models.currentText()
        model = ModelFactory.create_model(model_name)()

        if isinstance(layer, Spectrum1DRefModelLayer):
            mask = self.active_window.get_roi_mask(layer._parent)

            # pass Quantity arrays: BlackBody model needs to know the units.
            initialize(model, layer._parent.masked_dispersion[mask].compressed(),
                       layer._parent.masked_data[mask].compressed())
            # The layer is a `ModelLayer`, in which case, additionally
            # add the model to the compound model and update plot
            if layer.model is not None:
                layer.model = layer.model + model
            else:
                layer.model = model
        else:
            mask = self.active_window.get_roi_mask(layer)

            # pass Quantity arrays: BlackBody model needs to know the units.
            initialize(model, layer.masked_dispersion[mask].compressed(),
                       layer.masked_data[mask].compressed())

            # If a layer is selected, but it's not a `ModelLayer`,
            # create a new `ModelLayer`
            layer = self.add_model_layer(model=model)

        dispatch.on_update_model.emit(layer=layer)
        dispatch.on_add_model.emit(layer=layer)

    def add_model_layer(self, model):
        """
        Creates a new layer object using the currently defined model.
        """
        layer = self.current_layer

        if layer is None:
            return

        # compound_model = self.get_compound_model(
        #     model_dict=model_inputs,
        #     formula=self.contents.line_edit_model_arithmetic.text())

        # Create new layer using current ROI masks, if they exist
        # mask = self.active_window.get_roi_mask(layer=layer)

        new_model_layer = Spectrum1DRefModelLayer.from_parent(
            parent=layer,
            model=model,
            # layer_mask=mask
        )

        dispatch.on_add_layer.emit(layer=new_model_layer,
                                   window=self.active_window)

        return new_model_layer

    @dispatch.register_listener("on_add_model")
    def add_model_item(self, layer=None, model=None, unique=True):
        """
        Adds an `astropy.modeling.Model` to the loaded model tree widget.

        Parameters
        ----------
        """
        if layer is not None:
            self.contents.tree_widget_current_models.clear()

            if hasattr(layer.model, '_submodels'):
                models = layer.model._submodels
            else:
                models = [layer.model]
        elif model is not None:
            models = [model]
        else:
            return

        self.contents.tree_widget_current_models.clear()

        for model in models:
            if model is None:
                continue

            if unique:
                if self.get_model_item(model) is not None:
                    continue

            name = model.name

            if not name:
                count = 0

                root = self.contents.tree_widget_current_models.invisibleRootItem()

                for i in range(root.childCount()):
                    child = root.child(i)
                    pre_mod = child.data(0, Qt.UserRole)
                    pre_name = child.text(0)

                    if isinstance(model, pre_mod.__class__):
                        cur_num = next(iter([int(x) for x in re.findall(r'\d+', pre_name)]), 0) + 1

                        if cur_num > count:
                            count = cur_num

                name = model.__class__.__name__.replace('1D', '') + str(count)
                model._name = name

            new_item = QTreeWidgetItem()
            new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)

            new_item.setText(0, name)
            new_item.setData(0, Qt.UserRole, model)

            for i, para in enumerate(model.param_names):
                new_para_item = QTreeWidgetItem(new_item)
                new_para_item.setText(0, para)
                new_para_item.setData(0, Qt.UserRole, para)
                new_para_item.setData(1, Qt.UserRole, model.parameters[i])
                new_para_item.setText(1, "{:g}".format(model.parameters[i]))
                new_para_item.setFlags(new_para_item.flags() |
                                       Qt.ItemIsEditable |
                                       Qt.ItemIsUserCheckable)

                new_para_item.setCheckState(2, Qt.Checked if model.fixed.get(para)
                                                          else Qt.Unchecked)

            self.contents.tree_widget_current_models.addTopLevelItem(new_item)
            self.contents.tree_widget_current_models.expandItem(new_item)

        self._update_arithmetic_text(layer)

    @dispatch.register_listener("on_update_model")
    def update_model_item(self, layer):
        if hasattr(layer.model, '_submodels'):
            models = layer.model._submodels
        else:
            models = [layer.model]

        for model in models:
            model_item = self.get_model_item(model)

            if model_item is None:
                return

            for i, para in enumerate(model.param_names):
                for i in range(model_item.childCount()):
                    param_item = model_item.child(i)

                    if param_item.text(0) == para:
                        param_item.setText(1, "{:g}".format(
                            model.parameters[i]))

        # turn signals back on after fitting a model and
        # update the layer without validation
        if self.contents.tree_widget_current_models.signalsBlocked():
            self.current_layer.model = layer.model
            self.contents.tree_widget_current_models.blockSignals(False)

    @dispatch.register_listener("on_remove_model")
    def remove_model_item(self, model=None):
        if model is None:
            model = self.current_model

        # Remove model from submodels of compound model
        layer = self.current_layer

        if hasattr(layer, '_model') and hasattr(layer.model, '_submodels'):
            [layer.model._submodels.remove(x) for x in layer.model._submodels
             if x.name == model.name]
        else:
            layer.model = None

        # Remove model from tree widget
        root = self.contents.tree_widget_current_models.invisibleRootItem()

        for i in range(root.childCount()):
            child = root.child(i)

            if child.data(0, Qt.UserRole) == model:
                root.removeChild(child)
                break

            for j in range(child.childCount()):
                sec_child = child.child(j)

                if sec_child.data(0, Qt.UserRole) == model:
                    child.removeChild(sec_child)
                    break

        self.update_model_formula()
        self.toggle_fitting()

    def get_model_item(self, model):
        root = self.contents.tree_widget_current_models.invisibleRootItem()

        for i in range(root.childCount()):
            child = root.child(i)

            if child.data(0, Qt.UserRole) == model:
                return child

    def get_model_inputs(self):
        """
        Returns the model and current parameters displayed in the UI.

        Returns
        -------
        models : dict
            A dictionary with the model instance as the key and a list of
            floats as the parameters values.
        """
        root = self.contents.tree_widget_current_models.invisibleRootItem()
        models = {}

        for model_item in [root.child(j) for j in range(root.childCount())]:
            model = model_item.data(0, Qt.UserRole)
            args = []

            for i in range(model_item.childCount()):
                child_item = model_item.child(i)
                child = child_item.text(1)

                args.append(float(child))

            models[model] = args

        return models

    def update_model_formula(self):
        model_layer = self.current_layer

        model_dict = self.get_model_inputs()
        model = self.get_compound_model(model_dict=model_dict)

        if model is None:
            dispatch.on_update_model.emit(layer=model_layer)
            return

        model_layer.model = model

        dispatch.on_update_model.emit(layer=model_layer)

    def get_compound_model(self, model_dict=None, formula=''):
        model_dict = model_dict or self.get_model_inputs()
        formula = formula or self.contents.line_edit_model_arithmetic.text()
        models = []

        for model in model_dict:
            for i, param_name in enumerate(model.param_names):
                setattr(model, param_name, model_dict[model][i])

            models.append(model)

        if len(models) == 0:
            return

        if formula:
            model = Spectrum1DRefModelLayer.from_formula(models, formula)
            return model

        return np.sum(models) if len(models) > 1 else models[0]

    @dispatch.register_listener("on_update_model")
    def _update_arithmetic_text(self, layer):
        if hasattr(layer, '_model'):
            # If the model is a compound
            if hasattr(layer.model, '_submodels'):
                expr = layer.model._format_expression()
                expr = expr.replace('[', '{').replace(']', '}')

                model_names = [model.name
                               for model in layer.model._submodels]

                expr = expr.format(*model_names)
            # If it's just a single model
            else:
                expr = layer.model.name if layer.model is not None else ""

            self.contents.line_edit_model_arithmetic.setText(expr)

            return expr

    @dispatch.register_listener("on_selected_model", "on_changed_model")
    def _update_model_name(self, model_item, col=0):
        if model_item is None:
            return

        model = model_item.data(0, Qt.UserRole)

        if hasattr(model, '_name'):
            name = model_item.text(0)
            all_names = self.contents.tree_widget_current_models.findItems(
                name, Qt.MatchExactly, 0)

            if len(all_names) > 1:
                name = "{}{}".format(name, len(all_names) - 1)

            # Remove whitespace
            name = name.replace(" ", "_")

            model._name = name

            self.contents.tree_widget_current_models.blockSignals(True)
            model_item.setText(0, name)
            self.contents.tree_widget_current_models.blockSignals(False)

        self._update_arithmetic_text(self.current_layer)

    @dispatch.register_listener("on_changed_model")
    def _update_model_parameters(self, *args, **kwargs):
        model_layer = self.current_layer
        model_dict = self.get_model_inputs()

        model = self.get_compound_model(model_dict=model_dict,
                                        formula=self.contents.line_edit_model_arithmetic.text())

        if model is not None:
            model_layer.model = model

            dispatch.on_update_model.emit(layer=model_layer)
        else:
            logging.error("Cannot set `ModelLayer` model to new compound "
                          "model.")

    @dispatch.register_listener("on_selected_layer")
    def update_model_list(self, layer_item=None, layer=None):
        self.contents.tree_widget_current_models.clear()
        self.contents.line_edit_model_arithmetic.clear()

        if layer_item is None and layer is None:
            return

        layer = layer or layer_item.data(0, Qt.UserRole)

        if not hasattr(layer, '_model'):
            return

        self.add_model_item(layer)

    def _model_parameter_validation(self, model_item, col=1):
        if col == 2:
            return

        try:
            txt = "{:g}".format(float(model_item.text(col)))
            model_item.setText(col, txt)
            model_item.setData(col, Qt.UserRole, float(model_item.text(col)))
        except ValueError:
            prev_val = model_item.data(col, Qt.UserRole)
            model_item.setText(col, str(prev_val))

        dispatch.on_changed_model.emit(model_item=model_item)

    def _fix_model_parameter(self, model_item, col=0):
        parent = model_item.parent()

        if col == 2 and parent is not None:
            model = parent.data(0, Qt.UserRole)
            param = getattr(model, model_item.text(0))
            param.fixed = bool(model_item.checkState(col))
            dispatch.on_changed_model.emit(model_item=model_item)

    def _compose_fit_kwargs(self):
        return {
            'maxiter': int(self.contents.max_iterations_line_edit.text()),
            'acc': float(self.contents.relative_error_line_edit.text()),
            'epsilon': float(self.contents.epsilon_line_edit.text())
        }

    def fit_model_layer(self):
        current_layer = self.current_layer

        if not isinstance(current_layer, Spectrum1DRefModelLayer):
            logging.error("Attempting to fit model on a non ModelLayer.")
            return

        # This would allow updating the mask on the model layer to reflect
        # the current rois on the plot. Useful for directing fitting,
        # but may be unintuitive.
        mask = self.active_window.get_roi_mask(layer=current_layer._parent)
        # current_layer._layer_mask = mask

        # Update the model parameters with those in the gui
        # self.update_model_layer()

        # block signals before fitting to stop from reading
        # model parameters from UI
        self.contents.tree_widget_current_models.blockSignals(True)
        # Create fitted layer
        self.fit_model_thread(
            model_layer=current_layer,
            fitter_name=self.contents.combo_box_fitting.currentText(),
            mask=mask,
            kwargs=self._compose_fit_kwargs()
        )

        self.fit_model_thread.start()

    def toggle_buttons(self):
        root = self.contents.tree_widget_current_models.invisibleRootItem()

        if root.childCount() > 0:
            self.contents.button_remove_model.setEnabled(True)
        else:
            self.contents.button_remove_model.setEnabled(False)

    # this is also called in response to the "on_remove_model" signal,
    # however indirectly via the remove_model_item method.
    @dispatch.register_listener("on_add_model")
    def toggle_fitting(self, *args, **kwargs):
        root = self.contents.tree_widget_current_models.invisibleRootItem()

        if root.childCount() > 0:
            self.contents.group_box_fitting.setEnabled(True)
            self.contents.button_save_model.setEnabled(True)
            self.contents.button_export_model.setEnabled(True)
        else:
            self.contents.group_box_fitting.setEnabled(False)
            self.contents.button_save_model.setEnabled(False)
            self.contents.button_export_model.setEnabled(True)

    @dispatch.register_listener("on_selected_layer")
    def toggle_io(self, layer_item, *args, **kwargs):
        if layer_item:
            self.contents.button_load_model.setEnabled(True)
        else:
            self.contents.button_load_model.setEnabled(False)

    # ---
    # IO
    def _prepare_model_for_save(self):
        model_dict = self.get_model_inputs()
        formula = self.contents.line_edit_model_arithmetic.text()

        if len(model_dict) == 0:
            return None, None

        return self.get_compound_model(model_dict,
                                       formula=formula), formula

    def get_model_dict(self):
        model, formula = self._prepare_model_for_save()
        roi_bounds = self.active_window.get_roi_bounds()

        if model:
            out_model_dict = yaml_model_io.saveModelToFile(self,
                                                           model,
                                                           model_directory=None,
                                                           expression=formula,
                                                           roi_bounds=roi_bounds)

            return out_model_dict

    def save_model(self):
        model, formula = self._prepare_model_for_save()
        roi_bounds = self.active_window.get_roi_bounds()

        if model:
            global _model_directory
            yaml_model_io.saveModelToFile(self,
                                          model,
                                          _model_directory,
                                          expression=formula,
                                          roi_bounds=roi_bounds)

    def export_model(self):
        model, formula = self._prepare_model_for_save()

        if model:
            global _model_directory
            py_model_io.saveModelToFile(self,
                                        model,
                                        _model_directory,
                                        expression=formula)

    @dispatch.register_listener("load_model_from_dict")
    def load_model(self, model_dict=None):
        if model_dict is None:
            global _model_directory
            fname = compat.getopenfilenames(parent=self,
                                            caption='Read model file',
                                            basedir=_model_directory,
                                            filters=yaml_model_io.MODEL_FILE_FILTER)

            # File dialog returns a tuple with a list of file names.
            # We get the first name from the first tuple element.
            if len(fname[0]) < 1:
                return
            fname = fname[0][0]

            compound_model, formula, roi_bounds = yaml_model_io.buildModelFromFile(fname)
        else:
            compound_model, formula, roi_bounds = yaml_model_io.build_model_from_dict(model_dict)

        # Put new model in its own sub-layer under current layer.
        current_layer = self.current_layer

        if current_layer is None:
            return

        # Create new model layer using current ROI masks, if they exist
        mask = self.active_window.get_roi_mask(layer=current_layer)

        current_window = self.active_window

        # If there already is a model layer, just edit its model
        if hasattr(current_layer, '_model'):
            current_layer.model = compound_model

            self.update_model_list(layer=current_layer)
            dispatch.on_update_model.emit(layer=current_layer)
        else:
            layer = self.add_model_layer(compound_model)

            dispatch.on_update_model.emit(layer=layer)
            dispatch.on_add_model.emit(layer=layer)
            # dispatch.on_remove_model.emit(layer=layer)

        for bound in roi_bounds:
            current_window.add_roi(bounds=bound)
