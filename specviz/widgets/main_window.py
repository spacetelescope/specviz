import os

from qtpy.QtWidgets import QMainWindow, QSizePolicy, QWidget, QApplication, QActionGroup
from qtpy.uic import loadUi

from .workspace import Workspace
from ..utils import UI_PATH
from . import resources

__all__ = ['MainWindow']


class UiMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(UiMainWindow, self).__init__(*args, **kwargs)

        # Load the ui file and attached it to this instance
        loadUi(os.path.join(UI_PATH, "main_window.ui"), self)

        # Add spacers to the main tool bar
        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        spacer.setSizePolicy(size_policy)
        self.tool_bar.insertWidget(self.load_data_action, spacer)

        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        spacer.setSizePolicy(size_policy)
        self.tool_bar.insertWidget(self.new_plot_action, spacer)

        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(3)
        spacer.setSizePolicy(size_policy)
        self.tool_bar.addWidget(spacer)

        # Setup plugin toolbar
        self._plugin_action_group = QActionGroup(self)
        self.model_editor_toggle.setActionGroup(self._plugin_action_group)
        self.statistics_toggle.setActionGroup(self._plugin_action_group)
        self.mask_editor_toggle.setActionGroup(self._plugin_action_group)

        # Hide the plugin dock initially
        self.plugin_dock.hide()

        # Create a default workspace
        self._workspace = Workspace()
        self.setCentralWidget(self._workspace)

        # Update title
        self.setWindowTitle(self._workspace.name + " — SpecViz")


class MainWindow(UiMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Setup connections
        self.setup_connections()

    def setup_connections(self):
        # Primary toolbar actions
        self.new_workspace_action.triggered.connect(lambda: MainWindow().show())
        self.new_plot_action.triggered.connect(self._on_new_plot)
        self.load_data_action.triggered.connect(self._on_load_data)

        # Plugin toolbar actions
        self._plugin_action_group.triggered.connect(self._on_toggle_plugin_dock)
        self.model_editor_toggle.triggered.connect(lambda: self._on_toggle_plugin("Model Editor"))
        self.statistics_toggle.triggered.connect(lambda: self._on_toggle_plugin("Statistics"))
        self.mask_editor_toggle.triggered.connect(lambda: self._on_toggle_plugin("Mask Editor"))

        self.plugin_dock.visibilityChanged.connect(self._on_plugin_dock_visbility_changed)

    def _on_new_plot(self):
        self._workspace.add_plot_window()

    def _on_load_data(self):
        pass

    def _on_toggle_plugin_dock(self):
        if self._plugin_action_group.checkedAction():
            self.plugin_dock.show()
        else:
            self.plugin_dock.hide()

    def _on_toggle_plugin(self, name):
        self.plugin_dock.setWindowTitle(name)

    def _on_plugin_dock_visbility_changed(self, visible):
        if not visible:
            for act in self._plugin_action_group.actions():
                act.setChecked(False)
