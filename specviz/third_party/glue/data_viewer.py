import os
from collections import OrderedDict

import numpy as np
from glue.core import message as msg
from glue.core import Subset
from glue.utils import nonpartial
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.viewers.common.qt.toolbar import BasicToolbar
from qtpy.QtCore import QSize, Qt
from qtpy.QtWidgets import QTabWidget, QVBoxLayout, QWidget
from spectral_cube import SpectralCube

from ...app import App
from ...core import dispatch
from ...core.data import Spectrum1DRef
from .layer_widget import LayerWidget
from .viewer_options import OptionsWidget

__all__ = ['SpecVizViewer']


class SpecVizViewer(DataViewer):
    LABEL = "SpecViz Viewer"

    def __init__(self, session, parent=None):
        super(SpecVizViewer, self).__init__(session, parent=parent)

        # Connect the dataview to the specviz messaging system
        dispatch.setup(self)

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
        self._layer_widget.ui.combo_active_layer.currentIndexChanged.connect(
            nonpartial(self._update_options))
        # self._layer_widget.ui.combo_active_layer.currentIndexChanged.connect(
        #     nonpartial(self._refresh_data))
        # self._options_widget.ui.combo_file_attribute.currentIndexChanged.connect(
        #     nonpartial(self._refresh_data))

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
            # tb['widget'].setToolButtonStyle(Qt.ToolButtonIconOnly)
            tb['widget'].setIconSize(QSize(24, 24))

        # Set the view mode of mdi area to tabbed so that user aren't confused
        mdi_area = self.viewer.main_window.mdi_area
        mdi_area.setViewMode(mdi_area.TabbedView)
        mdi_area.setDocumentMode(True)
        mdi_area.setTabPosition(QTabWidget.South)

        layer_list = self.viewer._instanced_plugins.get('Layer List')
        self._layer_list = layer_list.widget() if layer_list is not None else None

        model_fitting = self.viewer._instanced_plugins.get('Model Fitting')
        self._model_fitting = model_fitting.widget() if model_fitting is not None else None

        self._unified_options = QWidget()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._options_widget)
        layout.addWidget(self._layer_widget)
        layout.addWidget(self._layer_list)

        self._unified_options.setLayout(layout)

        self.setCentralWidget(self.viewer.main_window)

    # The following method is required by glue - it is used to subscribe the
    # viewer to various messages sent by glue.

    def register_to_hub(self, hub):
        super(SpecVizViewer, self).register_to_hub(hub)

        hub.subscribe(self, msg.SubsetCreateMessage,
                      handler=self._add_subset)

        hub.subscribe(self, msg.SubsetUpdateMessage,
                      handler=self._update_subset)

        hub.subscribe(self, msg.SubsetDeleteMessage,
                      handler=self._remove_subset)

        hub.subscribe(self, msg.DataUpdateMessage,
                      handler=self._update_data)

    def _spectrum_from_component(self, layer, component, wcs, mask=None):
        data = SpectralCube(component.data, wcs)

        if mask is not None:
            data = data.with_mask(mask)

        spec_data = data.sum((1, 2))

        spec_data = Spectrum1DRef(spec_data.data,
                                  unit=spec_data.unit,
                                  dispersion=data.spectral_axis.data,
                                  dispersion_unit=data.spectral_axis.unit,
                                  wcs=data.wcs)

        # Store the relation between the component and the specviz data. If
        # the data exists, first remove the component from specviz and then
        # re-add it.
        if layer in self._specviz_data_cache:
            old_spec_data = self._specviz_data_cache[layer]
            dispatch.on_remove_data.emit(old_spec_data)

        self._specviz_data_cache[layer] = spec_data

        dispatch.on_add_to_window.emit(spec_data)

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

        layer = self._layer_widget.layer
        cid = layer.id[self._options_widget.file_att]
        component = layer.get_component(cid)

        self._spectrum_from_component(layer, component, data.coords.wcs)

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

        subset = self._layer_widget.layer
        cid = subset.data.id[self._options_widget.file_att]
        mask = subset.to_mask()
        component = subset.data.get_component(cid)

        self._spectrum_from_component(subset, component,
                                      subset.data.coords.wcs, mask=mask)

    def _remove_subset(self, message):
        if message.subset in self._layer_widget:
            self._layer_widget.remove_layer(message.subset)

        subset = self._layer_widget.layer

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
