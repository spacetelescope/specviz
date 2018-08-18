# This is a data viewer for individual spectra - that is, the glue Data object
# should be 1-dimensional and have a spectral axis. For more information about
# how this viewer is written, see the following documentation page:
#
# Writing a custom viewer for glue with Qt
# http://docs.glueviz.org/en/latest/customizing_guide/qt_viewer.html

import os

import uuid

from qtpy.QtWidgets import QWidget, QMessageBox

from glue.core.data_combo_helper import ComponentIDComboHelper

from glue.external.echo import CallbackProperty, SelectionCallbackProperty, keep_in_sync
from glue.external.echo.qt import autoconnect_callbacks_to_qt

from glue.viewers.common.layer_artist import LayerArtist
from glue.viewers.common.state import ViewerState, LayerState
from glue.viewers.common.qt.data_viewer import DataViewer

from glue.utils.qt import load_ui

from .utils import glue_data_to_spectrum1d, is_glue_data_1d_spectrum
from ...widgets.main_window import MainWindow

__all__ = ['SpecvizSingleDataViewer']


class SpecvizSingleViewerState(ViewerState):

    y_att = SelectionCallbackProperty(docstring='The attribute to use on the y-axis')

    def __init__(self, *args, **kwargs):
        super(SpecvizSingleViewerState, self).__init__(*args, **kwargs)
        self._y_att_helper = ComponentIDComboHelper(self, 'y_att')
        self.add_callback('layers', self._on_layers_change)

    def _on_layers_change(self, value):
        self._y_att_helper.set_multiple_data(self.layers_data)


class SpecvizSingleLayerState(LayerState):

    color = CallbackProperty(docstring='The color used to display the data')
    alpha = CallbackProperty(docstring='The transparency used to display the data')

    def __init__(self, viewer_state=None, **kwargs):

        super(SpecvizSingleLayerState, self).__init__(viewer_state=viewer_state, **kwargs)

        self.color = self.layer.style.color
        self.alpha = self.layer.style.alpha

        self._sync_color = keep_in_sync(self, 'color', self.layer.style, 'color')
        self._sync_alpha = keep_in_sync(self, 'alpha', self.layer.style, 'alpha')


class SpecvizSingleLayerArtist(LayerArtist):

    _layer_state_cls = SpecvizSingleLayerState

    def __init__(self, specviz_window, *args, **kwargs):

        super(SpecvizSingleLayerArtist, self).__init__(*args, **kwargs)

        self.specviz_window = specviz_window
        self.plot_widget = self.specviz_window.workspace.current_plot_window.plot_widget

        self.state.add_callback('visible', self.update)

        # FIXME: at the moment the zorder is ignored, and we need to figure out
        # how to programmatically change this in specviz

        # self.state.add_callback('zorder', self.update)
        self._viewer_state.add_callback('y_att', self.update)

        # FIXME: at the moment changing the color causes the data to be removed
        # from and added back to Specviz - obviously we need to do this more
        # efficiently
        self.state.add_callback('color', self.update)
        self.state.add_callback('alpha', self.update)

        self.uuid = str(uuid.uuid4())

    def _on_visible_change(self, value=None):
        self.redraw()

    def _on_zorder_change(self, value=None):
        self.redraw()

    def remove(self):

        # FIXME: simplify the following by implementing DataListModel.remove_data
        # and making it able to take e.g. data name.

        data_model = self.specviz_window.workspace._model
        for i in range(data_model.rowCount()):
            item = data_model.item(i)
            if item.data() == self.uuid:
                data_model.removeRow(i)
                return

    def clear(self):
        self.remove()

    def redraw(self):
        pass

    @property
    def proxy_index(self):

        # FIXME: this and plot_data_item definitely needs to be simplified!

        data_model = self.specviz_window.workspace._model
        for i in range(data_model.rowCount()):
            item = data_model.item(i)
            if item.data() == self.uuid:
                break
        else:
            return None

        source_index = self.plot_widget.proxy_model.sourceModel().indexFromItem(item)
        proxy_index = self.plot_widget.proxy_model.mapFromSource(source_index)

        return proxy_index

    @property
    def plot_data_item(self):
        """
        Get the PlotDataItem corresponding to this layer artist.
        """

        # FIXME: this definitely needs to be simplified!

        proxy_index = self.proxy_index
        if proxy_index is None:
            return
        else:
            return self.specviz_window.workspace.proxy_model.item_from_index(proxy_index)

    def update(self, *args, **kwargs):

        if not is_glue_data_1d_spectrum(self.state.layer):
            self.disable('Not a 1D spectrum')
            return

        self.enable()

        spectrum = glue_data_to_spectrum1d(self.state.layer, self._viewer_state.y_att)

        if self.plot_data_item is None:
            self.specviz_window.workspace.model.add_data(spectrum, name=self.uuid)
            self.plot_widget.add_plot(self.plot_data_item, visible=True, initialize=True)
        else:
            self.plot_data_item.data_item.set_data(spectrum)

        self.plot_data_item.visible = self.state.visible

        self.plot_data_item.color = self.state.layer.style.color


class SpecvizSingleViewerStateWidget(QWidget):

    def __init__(self, viewer_state=None, session=None):

        super(SpecvizSingleViewerStateWidget, self).__init__()

        self.ui = load_ui('viewer_state.ui', self,
                          directory=os.path.dirname(__file__))

        self.viewer_state = viewer_state
        autoconnect_callbacks_to_qt(self.viewer_state, self.ui)


class SpecvizSingleLayerStateWidget(QWidget):

    def __init__(self, layer_artist):

        super(SpecvizSingleLayerStateWidget, self).__init__()

        self.ui = load_ui('layer_state.ui', self,
                          directory=os.path.dirname(__file__))

        connect_kwargs = {'alpha': dict(value_range=(0, 1))}

        autoconnect_callbacks_to_qt(layer_artist.state, self.ui, connect_kwargs)


class SpecvizSingleDataViewer(DataViewer):

    LABEL = 'Specviz viewer (single spectrum)'
    _state_cls = SpecvizSingleViewerState
    _options_cls = SpecvizSingleViewerStateWidget
    _layer_style_widget_cls = SpecvizSingleLayerStateWidget
    _data_artist_cls = SpecvizSingleLayerArtist
    _subset_artist_cls = SpecvizSingleLayerArtist

    def __init__(self, *args, **kwargs):
        super(SpecvizSingleDataViewer, self).__init__(*args, **kwargs)
        self.specviz_window = MainWindow()
        self.setCentralWidget(self.specviz_window)
        # FIXME: the following shouldn't be needed
        self.specviz_window.workspace._model.clear()

    def add_data(self, data):
        if not is_glue_data_1d_spectrum(data):
            QMessageBox.critical(self, "Error", "Data is not a 1D spectrum",
                                 buttons=QMessageBox.Ok)
            return False
        return super(SpecvizSingleDataViewer, self).add_data(data)

    def add_subset(self, subset):
        if not is_glue_data_1d_spectrum(subset):
            QMessageBox.critical(self, "Error", "Subset is not a 1D spectrum",
                                 buttons=QMessageBox.Ok)
            return False
        return super(SpecvizSingleDataViewer, self).add_subset(subset)

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        return cls(self.specviz_window, self.state, layer=layer, layer_state=layer_state)
