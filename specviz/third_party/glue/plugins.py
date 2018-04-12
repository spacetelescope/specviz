"""
Manage plot attributes
"""
import logging
import os
from collections import OrderedDict

import numpy as np
from astropy.units import Unit
from qtpy.QtWidgets import QDialog
from qtpy.uic import loadUi
from spectral_cube import BooleanArrayMask, SpectralCube
from glue.core import Subset, Data

from ...core.events import dispatch
from ...analysis.filters import SmoothingOperation
from ...widgets.dialogs import TopAxisDialog, UnitChangeDialog
from ...widgets.plugin import Plugin
from ...widgets.utils import ICON_PATH, UI_PATH
from .dialogs import SpectralOperationHandler


class SpectralOperationPlugin(Plugin):
    name = "CubeViz Operations"
    location = "hidden"
    priority = 0

    def __init__(self, *args, **kwargs):
        super(SpectralOperationPlugin, self).__init__(*args, **kwargs)
        self._current_model = None
        self._session = None
        self._layout = None
        self._data = None
        self._spectral_data = None
        self._component_id = None

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, value):
        self._session = value

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self, value):
        self._layout = value

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def component_id(self):
        return self._component_id

    @component_id.setter
    def component_id(self, value):
        self._component_id = value

    @property
    def spectral_data(self):
        return self._spectral_data

    @spectral_data.setter
    def spectral_data(self, value):
        self._spectral_data = value

    def setup_ui(self):
        self.add_tool_bar_actions(
            name="Apply to Cube",
            description='Apply latest function to cube',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='CubeViz Operations',
            enabled=True,
            callback=self.apply_to_cube)

        self.add_tool_bar_actions(
            name="Collapse Cube",
            description='Collapse the cube over wavelength region',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='CubeViz Operations',
            enabled=True,
            callback=lambda: self.layout._open_dialog('Collapse Cube', None))

        self.add_tool_bar_actions(
            name="Fitted Linemap",
            description='Apply latest function to cube',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='CubeViz Operations',
            enabled=True,
            callback=self.create_fitted_linemap)

    @dispatch.register_listener("on_update_model")
    def on_model_updated(self, layer):
        self._current_model = layer.model

    def setup_connections(self):
        pass

    def apply_to_cube(self):
        # Send the operation stack, ensure reverse order so newer operations
        # are first
        dispatch.apply_operations.emit(
            stack=SmoothingOperation.operations()[::-1])

    def create_simple_linemap(self):

        def threadable_function(data, tracker):
            out = np.empty(shape=data.shape)
            mask = self.active_window.get_roi_mask(layer=self.current_layer)

            for x in range(data.shape[1]):
                for y in range(data.shape[2]):
                    out[:, x, y] = np.sum(data[:, x, y][mask])

                    tracker()

            return out

        spectral_operation = SpectralOperationHandler(
            data=self.data,
            function=threadable_function,
            operation_name="Simple Linemap",
            component_id=self.component_id,
            layout=self.layout,
            ui_settings={
                'title': "Simple Linemap Operation",
                'group_box_title': "Choose the component to use for linemap "
                                   "generation",
                'description': "Sums the values of the chosen component in the "
                               "range of the current ROI in the spectral view "
                               "for each spectrum in the data cube."})

        spectral_operation.exec_()

    def create_fitted_linemap(self):

        def threadable_function(data, tracker):
            from astropy.modeling.fitting import LevMarLSQFitter

            out = np.empty(shape=data.shape)
            mask = self.active_window.get_roi_mask(layer=self.current_layer)
            spectral_axis = data.spectral_axis
            model = self._current_model

            # TODO: this is a temporary solution to handle the astropy 3.0.1
            # regression concerning compound models and units
            class ModelWrapper(model.__class__):
                @property
                def _supports_unit_fitting(self):
                    return True

            model = ModelWrapper()

            for x in range(data.shape[1]):
                for y in range(data.shape[2]):
                    flux = data[:, x, y]

                    fitter = LevMarLSQFitter()
                    fit_model = fitter(model,
                                       spectral_axis[mask],
                                       flux[mask])

                    new_data = fit_model(spectral_axis[mask])

                    out[:, x, y] = np.sum(new_data)

                    tracker()

            return out

        if self._current_model is None:
            dialog = QDialog()
            loadUi(os.path.join(os.path.dirname(__file__), "no_model_error_dialog.ui"), dialog)
            dialog.exec_()

            return

        spectral_operation = SpectralOperationHandler(
            data=self.data,
            function=threadable_function,
            operation_name="Fitted Linemap",
            component_id=self.component_id,
            layout=self.layout,
            ui_settings={
                'title': "Fitted Linemap Operation",
                'group_box_title': "Choose the component to use for linemap "
                                   "generation",
                'description': "Fits the current model to the values of the "
                               "chosen component in the range of the current "
                               "ROI in the spectral view for each spectrum in "
                               "the data cube."})

        spectral_operation.exec_()