import os

from astropy.io import registry as io_registry
from qtpy import compat
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTabBar, QWidget, QAction, QColorDialog
from qtpy.uic import loadUi

from specutils import Spectrum1D

from ..core.models import DataListModel, PlotProxyModel
from ..utils import UI_PATH
from .plotting import PlotWindow


class Workspace(QWidget):
    """
    A widget representing the primary interaction area for a given workspace.
    This includes the :class:`~qtpy.QtWidgets.QListView`, and the
    :class:`~qtpy.QtWigets.QMdiArea` widgets, and associated model information.
    """
    def __init__(self, *args, **kwargs):
        super(Workspace, self).__init__(*args, **kwargs)
        self._name = "Untitled Workspace"

        # Load the ui file and attach it to this instance
        loadUi(os.path.join(UI_PATH, "workspace.ui"), self)

        # Define a new data list model for this workspace
        self._model = DataListModel()

        # Don't expand mdiarea tabs
        self.mdi_area.findChild(QTabBar).setExpanding(True)

        # Add an initially empty plot
        self.add_plot_window()

        # Setup listview context menu
        self._toggle_visibility_action = QAction("Visible", parent=self)
        self._toggle_visibility_action.setCheckable(True)
        self._change_color_action = QAction("Change Color", parent=self)

        self.list_view.addAction(self._change_color_action)
        self.list_view.addAction(self._toggle_visibility_action)

        # When the current subwindow changes, mount that subwindow's proxy model
        self.mdi_area.subWindowActivated.connect(self._on_sub_window_activated)

        self._toggle_visibility_action.triggered.connect(self._on_toggle_visibility)
        self._change_color_action.triggered.connect(self._on_changed_color)

    @property
    def name(self):
        """The name of this workspace."""
        return self._name

    @property
    def model(self):
        """
        The data model for this workspace.

        .. note:: there is always at most one model per workspace.
        """
        return self._model

    @property
    def proxy_model(self):
        return self.current_plot_window.proxy_model

    @property
    def current_plot_window(self):
        return self.mdi_area.currentSubWindow() or self.mdi_area.subWindowList()[0]

    def add_plot_window(self):
        """
        Creates a new plot widget sub window and adds it to the workspace.
        """
        plot_window = PlotWindow(model=self.model, parent=self.mdi_area)
        self.list_view.setModel(plot_window.plot_widget.proxy_model)

        plot_window.setWindowTitle(plot_window._plot_widget.name)
        plot_window.setAttribute(Qt.WA_DeleteOnClose)

        self.mdi_area.addSubWindow(plot_window)
        plot_window.showMaximized()

    def _on_sub_window_activated(self, window):
        if window is not None:
            self.list_view.setModel(window.proxy_model)

    def _on_toggle_visibility(self, state):
        idx = self.list_view.currentIndex()
        item = self.proxy_model.data(idx, role=Qt.UserRole)

        item.visible = state

        self.proxy_model.dataChanged.emit(idx, idx)

    def _on_changed_color(self, color):
        color = QColorDialog.getColor()

        if color.isValid():
            idx = self.list_view.currentIndex()
            item = self.proxy_model.data(idx, role=Qt.UserRole)

            item.color = color.name()

            self.proxy_model.dataChanged.emit(idx, idx)

    def _on_new_plot(self):
        self.add_plot_window()

    def _on_load_data(self):
        filters = [x + " (*)" for x in io_registry.get_formats(Spectrum1D)['Format']]

        file_path, fmt = compat.getopenfilename(parent=self,
                                                caption="Load spectral data file",
                                                filters=";;".join(filters))

        if not file_path:
            return

        spec = Spectrum1D.read(file_path, format=fmt.split()[0])

        name = file_path.split('/')[-1].split('.')[0]

        self.model.add_data(spec, name=name)

    def _on_delete_data(self):
        proxy_idx = self.list_view.currentIndex()
        model_idx = self.proxy_model.mapToSource(proxy_idx)

        self.model.removeRow(model_idx.row())
