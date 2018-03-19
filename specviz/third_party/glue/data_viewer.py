import os
from collections import OrderedDict

import numpy as np
from astropy.modeling.fitting import LevMarLSQFitter
from glue.core import message as msg
from glue.core import Data, Subset
from glue.core.exceptions import IncompatibleAttribute
from glue.core.subset_group import GroupedSubset
from glue.utils import nonpartial
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.toolbar import BasicToolbar
from qtpy.QtCore import QSize, Qt
from qtpy.QtWidgets import (QComboBox, QDialog, QFormLayout, QTabBar,
                            QTabWidget, QToolButton, QVBoxLayout, QWidget)
from qtpy.uic import loadUi
from spectral_cube import SpectralCube

from ...analysis.filters import SmoothingOperation
from ...analysis.operations import FunctionalOperation
from ...app import App
from ...core import dispatch
from ...core.data import Spectrum1DRef
from ...interfaces.model_io.yaml_model_io import build_model_from_dict
from ...widgets.plugin import Plugin
from ...widgets.utils import ICON_PATH, UI_PATH
from .layer_widget import LayerWidget
from .viewer_options import OptionsWidget

__all__ = ['SpecVizViewer']


dispatch.register_event("toggle_component_visibility", ["data", "state"])


class SpecVizViewer(DataViewer):
    LABEL = "SpecViz Viewer"

    def __init__(self, session, parent=None):
        super(SpecVizViewer, self).__init__(session, parent=parent)

        # Connect the dataview to the specviz messaging system
        dispatch.setup(self)

        # Store a list of the current ROIs visible on SpecViz
        self._rois = []

        # We now set up the options widget. This controls for example which
        # attribute should be used to indicate the filenames of the spectra.
        self._options_widget = OptionsWidget(data_viewer=self)

        # The layer widget is used to select which data or subset to show.
        # We don't use the default layer list, because in this case we want to
        # make sure that only one dataset or subset can be selected at any one
        # time.
        self._layer_widget = LayerWidget()

        # Make sure we update the viewer if either the selected layer or the
        # column specifying the filename is changed.
        # self._layer_widget.ui.combo_active_layer.currentIndexChanged.connect(
        #     nonpartial(self._update_options))
        # self._layer_widget.ui.combo_active_layer.currentIndexChanged.connect(
        #     nonpartial(self._refresh_data))
        self._options_widget.ui.combo_file_attribute.currentIndexChanged.connect(
            self._on_operation_changed)

        # We keep a cache of the specviz data objects that correspond to a given
        # filename - although this could take up a lot of memory if there are
        # many spectra, so maybe this isn't needed
        self._specviz_data_cache = OrderedDict()

        # We set up the specviz viewer and controller as done for the standalone
        # specviz application
        self.viewer = App(disabled={'Data List': True},
                          hidden={'Layer List': True,
                                  'Statistics': True,
                                  'Model Fitting': True,
                                  'Mask Editor': True,
                                  'Data List': True},
                          menubar=False)

        # Remove Glue's viewer status bar
        self.statusBar().hide()

        # Make the main toolbar smaller to fit better inside Glue
        for tb in self.viewer._all_tool_bars.values():
            tb['widget'].setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            tb['widget'].setIconSize(QSize(20, 20))

            for child in tb['widget'].children():
                if isinstance(child, QToolButton):
                    child.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        # Set the view mode of mdi area to tabbed so that user aren't confused
        mdi_area = self.viewer.main_window.mdi_area
        mdi_area.setViewMode(mdi_area.TabbedView)
        mdi_area.setDocumentMode(True)
        mdi_area.setTabPosition(QTabWidget.South)
        mdi_area.setTabsClosable(True)

        # Hide the tab bar
        # mdi_area.findChild(QTabBar).hide()

        layer_list = self.viewer._instanced_plugins.get('Layer List')
        self._layer_list = layer_list.widget() if layer_list is not None else None

        model_fitting = self.viewer._instanced_plugins.get('Model Fitting')
        self._model_fitting = model_fitting.widget() if model_fitting is not None else None

        # Create combo box to hold the types of data summation that can be done
        self._data_operation = QComboBox()
        self._data_operation.addItems(['Sum', 'Mean', 'Median'])

        self._data_operation.currentIndexChanged.connect(
            self._on_operation_changed)

        data_op_form = QFormLayout()
        data_op_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self._unified_options = QWidget()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(data_op_form)
        # layout.addWidget(self._layer_widget)
        layout.addWidget(self._options_widget)
        data_op_form.addRow("Collapse Operation", self._data_operation)
        layout.addWidget(self._layer_list)

        self._unified_options.setLayout(layout)

        self.setCentralWidget(self.viewer.main_window)

    # The following method is required by glue - it is used to subscribe the
    # viewer to various messages sent by glue.

    def register_to_hub(self, hub):
        super(SpecVizViewer, self).register_to_hub(hub)

        # We only listen to subset creation and deletion for subsets for which
        # the data is already present as a layer in Specviz.

        hub.subscribe(self, msg.SubsetCreateMessage,
                      handler=self._add_subset,
                      filter=self._has_data)

        hub.subscribe(self, msg.SubsetUpdateMessage,
                      handler=self._update_subset,
                      filter=self._has_data)

        hub.subscribe(self, msg.SubsetDeleteMessage,
                      handler=self._remove_subset,
                      filter=self._has_data)

        hub.subscribe(self, msg.DataUpdateMessage,
                      handler=self._update_data,
                      filter=self._has_data)

    def _has_data(self, message):
        if isinstance(message.sender, Data):
            return message.sender in self._specviz_data_cache
        elif isinstance(message.sender, Subset):
            return message.sender.data in self._specviz_data_cache
        else:
            return False

    def _has_subset(self, message):
        if isinstance(message.sender, Subset):
            return message.sender in self._specviz_data_cache
        else:
            return False

    @dispatch.register_listener("added_roi")
    def _on_added_roi(self, roi):
        self._rois.append(roi)

    @dispatch.register_listener("removed_roi")
    def _on_removed_roi(self, roi):
        self._rois.remove(roi)

    @property
    def rois(self):
        """
        Returns the current list of ROIs on the SpecViz Viewer.
        """
        return self._rois

    @property
    def roi_bounds(self):
        """
        Returns a list of tuples with the current upper and lower bounds of
        each ROI in the SpecViz viewer.
        """
        return [roi.getRegion() for roi in self._rois]

    def _on_operation_changed(self, index):
        for layer in self._specviz_data_cache:
            if issubclass(layer.__class__, Subset):
                cid = layer.data.id[self._options_widget.file_att]
                component = layer.data.get_component(cid)
                try:
                    mask = layer.to_mask()
                except IncompatibleAttribute:
                    mask = np.zeros(layer.shape, dtype=bool)
                wcs = layer.data.coords.wcs
            else:
                cid = layer.id[self._options_widget.file_att]
                component = layer.get_component(cid)
                mask = None
                wcs = layer.coords.wcs

            self._spectrum_from_component(layer, component, wcs, mask=mask)

    def _spectrum_from_component(self, layer, component, wcs, mask=None):
        data = SpectralCube(component.data, wcs)

        if mask is not None:
            data = data.with_mask(mask)

        if self._data_operation.currentIndex() == 1:
            spec_data = data.mean((1, 2))
        elif self._data_operation.currentIndex() == 2:
            spec_data = data.median((1, 2))
        else:
            spec_data = data.sum((1, 2))

        spec_data = Spectrum1DRef(spec_data.data,
                                  unit=spec_data.unit,
                                  dispersion=data.spectral_axis.data,
                                  dispersion_unit=data.spectral_axis.unit,
                                  wcs=data.wcs,
                                  name=layer.label)

        # Store the relation between the component and the specviz data. If
        # the data exists, first remove the component from specviz and then
        # re-add it.
        if layer in self._specviz_data_cache:
            old_spec_data = self._specviz_data_cache[layer]
            dispatch.on_remove_data.emit(old_spec_data)

        self._specviz_data_cache[layer] = spec_data

        dispatch.on_add_to_window.emit(data=spec_data,
                                       style={'color': layer.style.rgba[:3]})

    def _update_combo_boxes(self, data):
        if data not in self._layer_widget:
            self._layer_widget.add_layer(data)

        self._layer_widget.layer = data
        self._options_widget.set_data(self._layer_widget.layer)

        if self._options_widget.file_att is None:
            return False

        if self._layer_widget.layer is None:
            return False

        return True

    # The following two methods are required by glue - they are what gets called
    # when a dataset or subset gets dragged and dropped onto the viewer.

    def add_data(self, data):
        if not self._update_combo_boxes(data):
            return

        layer = data #self._layer_widget.layer
        cid = layer.id[self._options_widget.file_att]
        component = layer.get_component(cid)

        self._spectrum_from_component(layer, component, layer.coords.wcs)

        return True

    def add_subset(self, subset):
        # We avoid doing any real work here, as adding a subset does not
        # simultaneously add the subset mask. We therefore move the
        # functionality to the update subset method.
        return True

    # The following four methods are used to receive various messages related
    # to updates to data or subsets.

    def _update_data(self, message):
        print("Updating data")

    def _add_subset(self, message):
        self.add_subset(message.subset)

    def _update_subset(self, message):

        if not self._update_combo_boxes(message.subset):
            return

        subset = message.subset  #self._layer_widget.layer
        cid = subset.data.id[self._options_widget.file_att]
        try:
            mask = subset.to_mask()
        except IncompatibleAttribute:
            mask = np.zeros(subset.shape, dtype=bool)
        component = subset.data.get_component(cid)

        self._spectrum_from_component(subset, component,
                                      subset.data.coords.wcs, mask=mask)

    def _remove_subset(self, message):
        if message.subset in self._layer_widget:
            self._layer_widget.remove_layer(message.subset)

        subset = message.subset

        spec_data = self._specviz_data_cache.pop(subset)
        dispatch.on_remove_data.emit(spec_data)

    # When the selected layer is changed, we need to update the combo box with
    # the attributes from which the filename attribute can be selected. The
    # following method gets called in this case.

    def _update_options(self):
        self._options_widget.set_data(self._layer_widget.layer)

    def initialize_toolbar(self):
        pass

    def layer_view(self):
        return self._unified_options

    def options_widget(self):
        return self._model_fitting

    @dispatch.register_listener("toggle_component_visibility")
    def on_toggle_component_visibility(self, data, state):
        """
        Hide a display specviz spectrum provided a glue layer component.
        """
        spec_data = self._specviz_data_cache.get(data)

        dispatch.toggle_layer_visibility.emit(layer=spec_data, state=state)


class SpectralOperationPlugin(Plugin):
    name = "CubeViz Operations"
    location = "hidden"
    priority = 0

    def __init__(self, *args, **kwargs):
        super(SpectralOperationPlugin, self).__init__(*args, **kwargs)
        self._current_model = None

    def setup_ui(self):
        self.add_tool_bar_actions(
            name="Apply to Cube",
            description='Apply latest function to cube',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='CubeViz Operations',
            enabled=True,
            callback=self.apply_to_cube)

        self.add_tool_bar_actions(
            name="Simple Linemap",
            description='Apply latest function to cube',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='CubeViz Operations',
            enabled=True,
            callback=self.create_simple_linemap)

        self.add_tool_bar_actions(
            name="Fitted Linemap",
            description='Apply latest function to cube',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='CubeViz Operations',
            enabled=True,
            callback=self.create_fitted_linemap)

        # self.add_tool_bar_actions(
        #     name="Cube Slice",
        #     description='Apply latest function to cube',
        #     icon_path=os.path.join(ICON_PATH, "Export-48.png"),
        #     category='CubeViz Operations',
        #     enabled=True,
        #     callback=self.create_sliced_cube)

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
        linemap_operation = SimpleLinemapOperation(
            keep_shape=True, # Change to False to make this an overlay
            mask=self.active_window.get_roi_mask(layer=self.current_layer))

        dispatch.apply_operations.emit(
            stack=[linemap_operation])

    def create_fitted_linemap(self):
        if self._current_model is None:
            dialog = QDialog()
            loadUi(os.path.join(UI_PATH, "no_model_error_dialog.ui"), dialog)
            dialog.exec_()
            return

        # Ask user if they'd like to perform the fit interactively.
        # dialog = QDialog()
        # loadUi(os.path.join(UI_PATH, "fitted_linemap_dialog.ui"), dialog)

        # if dialog.exec_():
        #     if dialog.inspect_each_spaxel_check_box.isChecked():
        #         pass
        #     else:
        linemap_operation = FittedLinemapOperation(
            keep_shape=True, # Change to False to make this an overlay
            model=self._current_model,
            mask=self.active_window.get_roi_mask(layer=self.current_layer))

        dispatch.apply_operations.emit(
            stack=[linemap_operation])

    def create_sliced_cube(self):
        cube_slice_operation = CubeSliceOperation(
            mask=self.active_window.get_roi_mask(layer=self.current_layer),
            axis='cube')

        dispatch.apply_operations.emit(
            stack=[cube_slice_operation])



def fitted_linemap(data, spectral_axis, model, mask):
    # The `data` argument should be the spectral axis of the cube given
    # for a particular pixel position in spatial space
    fitter = LevMarLSQFitter()
    fit_model = fitter(model, 
                       spectral_axis[mask], 
                       data[mask])

    new_data = fit_model(spectral_axis)

    return np.sum(new_data[mask])


def simple_linemap(data, spectral_axis, mask=None):
    return np.sum(data[mask])


def cube_slice(data, spectral_axis, mask=None):
    spectral_axis = data.spectral_axis
    return data.spectral_slab(spectral_axis[mask][0], spectral_axis[mask][-1])


class FittedLinemapOperation(FunctionalOperation):
    def __init__(self, *args, **kwargs):
        super(FittedLinemapOperation, self).__init__(fitted_linemap, *args, **kwargs)


class SimpleLinemapOperation(FunctionalOperation):
    def __init__(self, *args, **kwargs):
        super(SimpleLinemapOperation, self).__init__(simple_linemap, *args, **kwargs)


class CubeSliceOperation(FunctionalOperation):
    def __init__(self, *args, **kwargs):
        super(CubeSliceOperation, self).__init__(cube_slice, *args, **kwargs)
