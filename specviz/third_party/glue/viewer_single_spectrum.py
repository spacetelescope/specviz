import os

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

from .utils import glue_data_to_spectrum1d
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
        self.state.add_callback('visible', self.update)
        self.state.add_callback('zorder', self.update)
        self._viewer_state.add_callback('y_att', self.update)

    def _on_visible_change(self, value=None):
        self.redraw()

    def _on_zorder_change(self, value=None):
        self.redraw()

    def clear(self):
        pass

    def remove(self):
        pass

    def redraw(self):
        pass

    def update(self, *args, **kwargs):
        spectrum = glue_data_to_spectrum1d(self.state.layer, self._viewer_state.y_att)
        self.specviz_window.workspace.model.add_data(spectrum, name='banana')


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

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        return cls(self.specviz_window, self.state, layer=layer, layer_state=layer_state)
