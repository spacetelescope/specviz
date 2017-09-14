import os
from collections import OrderedDict

from glue.core import Subset
from glue.viewers.common.qt.data_viewer import DataViewer
from glue.core import message as msg
from glue.utils import nonpartial
from glue.viewers.common.qt.toolbar import BasicToolbar

import astropy.units as u
from astropy.wcs.wcs import WCSSUB_SPECTRAL

from spectral_cube import SpectralCube

from qtpy.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from ...app import App
from ...core import dispatch
from ...core import DispatchHandle
from ...core.data import Spectrum1DRef

from .viewer_options import OptionsWidget
from .layer_widget import LayerWidget


__all__ = ['SpecVizViewer']


class SpecVizViewer(DataViewer):
    LABEL = "SpecViz Viewer"

    def __init__(self, session, parent=None):
        super(SpecVizViewer, self).__init__(session, parent=parent)

        # Connect the dataview to the specviz messaging system
        DispatchHandle.setup(self)

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
        self.viewer = App(disabled={'Data List': False},
                          hidden={'Layer List': True,
                                  'Statistics': True,
                                  'Model Fitting': True,
                                  'Mask Editor': True,
                                  'Data List': True})

        # Remove the menubar so that it does not interfere with Glue's
        self.viewer.main_window.menu_bar = None

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

    # The following two methods are required by glue - they are what gets called
    # when a dataset or subset gets dragged and dropped onto the viewer.

    def add_data(self, data):
        print("Adding data")
        if data not in self._layer_widget:
            self._layer_widget.add_layer(data)

        self._layer_widget.layer = data
        self._options_widget.set_data(self._layer_widget.layer)

        if self._options_widget.file_att is None:
            return

        if self._layer_widget.layer is None:
            return

        cid = self._layer_widget.layer.id[self._options_widget.file_att]
        mask = None
        component = self._layer_widget.layer.get_component(cid)

        print("Creating cube")
        data = SpectralCube(component.data, data.coords.wcs)

        print("Creating spectrum")
        spec_data = Spectrum1DRef(data.sum((1,2)), dispersion=data.spectral_axis.data,
                                  dispersion_unit=data.spectral_axis.unit,
                                  wcs=data.wcs)

        print("Send to SpecViz")
        dispatch.on_add_data.emit(spec_data)

        return True

    def add_subset(self, subset):
        print("Adding subset")
        if subset not in self._layer_widget:
            self._layer_widget.add_layer(subset)
        self._layer_widget.layer = subset
        self._options_widget.set_data(self._layer_widget.layer)

        if self._options_widget.file_att is None:
            return

        if self._layer_widget.layer is None:
            return

        subset = self._layer_widget.layer
        cid = subset.data.id[self._options_widget.file_att]
        mask = subset.to_mask(None)
        component = subset.data.get_component(cid)
        print(component)

        return True

    # The following four methods are used to receive various messages related
    # to updates to data or subsets.

    def _update_data(self, message):
        print("Updating data")

    def _add_subset(self, message):
        self.add_subset(message.subset)

    def _update_subset(self, message):
        print("Updating subset")

    def _remove_subset(self, message):
        if message.subset in self._layer_widget:
            self._layer_widget.remove_layer(message.subset)
        print("Removing subset")

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
