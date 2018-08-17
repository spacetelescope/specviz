import os

import uuid
import numpy as np
from qtpy.QtWidgets import QWidget, QVBoxLayout, QCheckBox

from glue.config import qt_client
from glue.core.data_combo_helper import ComponentIDComboHelper

from glue.external.echo import CallbackProperty, SelectionCallbackProperty
from glue.external.echo.qt import (connect_checkable_button,
                                   autoconnect_callbacks_to_qt)

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
    pass


class SpecvizSingleLayerArtist(LayerArtist):

    _layer_state_cls = SpecvizSingleLayerState

    def __init__(self, specviz_window, *args, **kwargs):

        super(SpecvizSingleLayerArtist, self).__init__(*args, **kwargs)

        self.specviz_window = specviz_window
        self.plot_widget = self.specviz_window.workspace.current_plot_window.plot_widget

        self.state.add_callback('visible', self.update)
        self.state.add_callback('zorder', self.update)
        self._viewer_state.add_callback('y_att', self.update)
        self.uuid = str(uuid.uuid4())

    def _on_visible_change(self, value=None):
        self.redraw()

    def _on_zorder_change(self, value=None):
        self.redraw()

    def clear(self):
        data_model = self.specviz_window.workspace._model
        for i in range(data_model.rowCount()):
            item = data_model.item(i)
            if item.data() == self.uuid:
                data_model.removeRow(i)
                return

    def remove(self):
        pass

    def redraw(self):
        pass

    @property
    def proxy_index(self):

        # FIXME: this definitely needs to be simplified!

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

        if self.plot_data_item is not None:
            self.clear()

        spectrum = glue_data_to_spectrum1d(self.state.layer, self._viewer_state.y_att)
        self.specviz_window.workspace.model.add_data(spectrum, name=self.uuid)
        self.plot_widget.add_plot(self.proxy_index, visible=True, initialize=True)

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
        self.layer_state = layer_artist.state


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

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        return cls(self.specviz_window, self.state, layer=layer, layer_state=layer_state)
