import os

from qtpy.QtWidgets import QWidget, QTabBar
from qtpy.uic import loadUi
from qtpy.QtCore import Qt

from ..core.models import DataListModel, PlotProxyModel
from .plotting import PlotWindow

from ..utils import UI_PATH


class Workspace(QWidget):
    def __init__(self, *args, **kwargs):
        super(Workspace, self).__init__(*args, **kwargs)
        self._name = "Untitled Workspace"

        # Load the ui file and attach it to this instance
        loadUi(os.path.join(UI_PATH, "workspace.ui"), self)

        # Define a new data list model for this workspace
        self._model = DataListModel()

        # Don't expand mdiarea tabs
        self.mdi_area.findChild(QTabBar).setExpanding(True)

    @property
    def name(self):
        return self._name

    @property
    def model(self):
        return self._model

    @property
    def proxy_model(self):
        return self.current_plot_window.proxy_model

    @property
    def current_plot_window(self):
        return self.mdi_area.currentSubWindow()

    def add_plot_window(self):
        plot_window = PlotWindow(model=self.model, parent=self.mdi_area)
        self.list_view.setModel(plot_window.plot_widget.proxy_model)

        plot_window.setWindowTitle(plot_window._plot_widget.name)
        plot_window.setAttribute(Qt.WA_DeleteOnClose)

        self.mdi_area.addSubWindow(plot_window)
        plot_window.showMaximized()
