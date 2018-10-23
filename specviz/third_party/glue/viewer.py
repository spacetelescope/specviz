# This is a data viewer for glue data objects that have a spectral axis. For
# more information about how this viewer is written, see the following
# documentation page:
#
# Writing a custom viewer for glue with Qt
# http://docs.glueviz.org/en/latest/customizing_guide/qt_viewer.html

import os

from collections import OrderedDict

from qtpy.QtWidgets import QWidget, QMessageBox, QApplication

from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.core.exceptions import IncompatibleAttribute

from glue.external.echo import CallbackProperty, SelectionCallbackProperty, keep_in_sync
from glue.external.echo.qt import autoconnect_callbacks_to_qt

from glue.viewers.common.layer_artist import LayerArtist
from glue.viewers.common.state import ViewerState, LayerState
from glue.viewers.common.qt.data_viewer import DataViewer

from glue.utils.qt import load_ui

from .utils import glue_data_to_spectrum1d, glue_data_has_spectral_axis
from ...widgets.workspace import Workspace
from ...app import Application

__all__ = ['SpecvizDataViewer']

FUNCTIONS = OrderedDict([('maximum', 'Maximum'),
                         ('minimum', 'Minimum'),
                         ('mean', 'Mean'),
                         ('median', 'Median'),
                         ('sum', 'Sum')])


class SpecvizViewerState(ViewerState):
    pass

class SpecvizLayerState(LayerState):

    color = CallbackProperty(docstring='The color used to display the data')
    alpha = CallbackProperty(docstring='The transparency used to display the data')
    linewidth = CallbackProperty(1, docstring='The width of the line for the data')

    attribute = SelectionCallbackProperty(docstring='The attribute to use for the spectrum')
    statistic = SelectionCallbackProperty(docstring='The statistic to use to collapse data')

    def __init__(self, viewer_state=None, **kwargs):

        super(SpecvizLayerState, self).__init__(viewer_state=viewer_state, **kwargs)

        self.color = self.layer.style.color
        self.alpha = self.layer.style.alpha

        self._sync_color = keep_in_sync(self, 'color', self.layer.style, 'color')
        self._sync_alpha = keep_in_sync(self, 'alpha', self.layer.style, 'alpha')

        self._att_helper = ComponentIDComboHelper(self, 'attribute')
        self.add_callback('layer', self._on_layer_change)
        self._on_layer_change()

        SpecvizLayerState.statistic.set_choices(self, list(FUNCTIONS))
        SpecvizLayerState.statistic.set_display_func(self, FUNCTIONS.get)

    def _on_layer_change(self, *args):
        if self.layer is None:
            self._att_helper.set_multiple_data([])
        else:
            self._att_helper.set_multiple_data([self.layer])


class SpecvizLayerArtist(LayerArtist):

    _layer_state_cls = SpecvizLayerState

    def __init__(self, specviz_window, *args, **kwargs):

        super(SpecvizLayerArtist, self).__init__(*args, **kwargs)

        self.specviz_window = specviz_window
        self.plot_widget = self.specviz_window.current_plot_window.plot_widget

        self.state.add_callback('attribute', self.update)
        self.state.add_callback('statistic', self.update)

        self.state.add_callback('zorder', self.update_visual)
        self.state.add_callback('visible', self.update_visual)
        self.state.add_callback('color', self.update_visual)
        self.state.add_callback('alpha', self.update_visual)
        self.state.add_callback('linewidth', self.update_visual)

        self.data_item = None

    def remove(self):
        if self.data_item is not None:
            self.specviz_window.model.remove_data(self.data_item.identifier)
            self.data_item = None

    def clear(self):
        self.remove()

    def redraw(self):
        pass

    @property
    def plot_data_item(self):
        """
        Get the PlotDataItem corresponding to this layer artist.
        """
        if self.data_item is None:
            return None
        else:
            return self.plot_widget.proxy_model.item_from_id(self.data_item.identifier)

    def update_visual(self, *args, **kwargs):
        plot_data_item = self.plot_data_item
        if plot_data_item is not None:
            plot_data_item.visible = self.state.visible
            plot_data_item.zorder = self.state.zorder
            plot_data_item.width = self.state.linewidth
            plot_data_item.color = self.state.layer.style.color

    def update(self, *args, **kwargs):

        if self.state.layer is None or self.state.attribute is None:
            return

        try:
            spectrum = glue_data_to_spectrum1d(self.state.layer, self.state.attribute, statistic=self.state.statistic)
        except IncompatibleAttribute:
            self.disable_invalid_attributes(self.state.attribute)
            return

        self.enable()

        if self.data_item is None:
            self.data_item = self.specviz_window.model.add_data(spectrum, name=self.state.layer.label)
            self.plot_widget.add_plot(self.plot_data_item, visible=True, initialize=True)
        else:
            self.plot_data_item.data_item.set_data(spectrum)
            # FIXME: we shouldn't have to call update_data manually
            # self.plot_data_item.update_data()

        self.update_visual()


class SpecvizViewerStateWidget(QWidget):

    def __init__(self, viewer_state=None, session=None):

        super(SpecvizViewerStateWidget, self).__init__()

        self.ui = load_ui('viewer_state.ui', self,
                          directory=os.path.dirname(__file__))

        self.viewer_state = viewer_state
        autoconnect_callbacks_to_qt(self.viewer_state, self.ui)


class SpecvizLayerStateWidget(QWidget):

    def __init__(self, layer_artist):

        super(SpecvizLayerStateWidget, self).__init__()

        self.ui = load_ui('layer_state.ui', self,
                          directory=os.path.dirname(__file__))

        connect_kwargs = {'alpha': dict(value_range=(0, 1))}

        autoconnect_callbacks_to_qt(layer_artist.state, self.ui, connect_kwargs)


class SpecvizDataViewer(DataViewer):

    LABEL = 'Specviz viewer'
    _state_cls = SpecvizViewerState
    _options_cls = SpecvizViewerStateWidget
    _layer_style_widget_cls = SpecvizLayerStateWidget
    _data_artist_cls = SpecvizLayerArtist
    _subset_artist_cls = SpecvizLayerArtist

    def __init__(self, *args, **kwargs):

        super(SpecvizDataViewer, self).__init__(*args, **kwargs)
        self.statusBar().hide()

        # Fake a current_workspace property so that plugins can mount
        self.specviz_window = Workspace()
        self.specviz_window.set_embedded(True)
        QApplication.instance().current_workspace = self.specviz_window

        # Add an intially empty plot window
        self.specviz_window.add_plot_window()

        # Load specviz plugins
        Application.load_local_plugins()

        self.setCentralWidget(self.specviz_window)

        # For some reason this causes the PlotWindow to no longer be part of the
        # workspace MDI area which then causes issues down the line.
        # self.setCentralWidget(self.plot_window)

        # FIXME: the following shouldn't be needed
        # self.specviz_window._model.clear()

    def add_data(self, data):
        if not glue_data_has_spectral_axis(data):
            QMessageBox.critical(self, "Error", "Data is not a 1D spectrum",
                                 buttons=QMessageBox.Ok)
            return False
        return super(SpecvizDataViewer, self).add_data(data)

    def add_subset(self, subset):
        if not glue_data_has_spectral_axis(subset):
            QMessageBox.critical(self, "Error", "Subset is not a 1D spectrum",
                                 buttons=QMessageBox.Ok)
            return False
        return super(SpecvizDataViewer, self).add_subset(subset)

    def get_layer_artist(self, cls, layer=None, layer_state=None):
        return cls(self.specviz_window, self.state, layer=layer, layer_state=layer_state)

    def initialize_toolbar(self):
        pass
