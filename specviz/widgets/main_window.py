import os

from qtpy.QtCore import QCoreApplication, QEvent, Signal
from qtpy.QtWidgets import (QActionGroup, QApplication, QMainWindow,
                            QSizePolicy, QWidget)
from qtpy.uic import loadUi

from . import resources
from ..core.hub import Hub
from ..utils import UI_PATH
from .workspace import Workspace

__all__ = ['MainWindow']


class MainWindow(QMainWindow):
    """
    Main window object for SpecViz. This represents a single "Workspace", and
    multiple main windows can exist in a single SpecViz session.

    Signals
    -------
    window_activated : :class:`~qtpy.QtWidgets.QMainWindow`
        Fired when a particular `QMainWindow` is activated.
    """
    window_activated = Signal(QMainWindow)

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

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

        # Setup workspace action connections
        self.new_workspace_action.triggered.connect(
            QApplication.instance().add_workspace)
        self.new_plot_action.triggered.connect(
            self.workspace._on_new_plot)

        # Setup data action connections
        self.load_data_action.triggered.connect(
            self.workspace._on_load_data)
        self.delete_data_action.triggered.connect(
            self.workspace._on_delete_data)

        # Setup plugin toolbar action actions
        self._plugin_action_group.triggered.connect(
            self._on_toggle_plugin_dock)
        self.model_editor_toggle.triggered.connect(
            lambda: self._on_toggle_plugin("Model Editor"))
        self.statistics_toggle.triggered.connect(
            lambda: self._on_toggle_plugin("Statistics"))
        self.mask_editor_toggle.triggered.connect(
            lambda: self._on_toggle_plugin("Mask Editor"))

        self.plugin_dock.visibilityChanged.connect(
            self._on_plugin_dock_visbility_changed)

    @property
    def workspace(self):
        """Return the workspace widget within this `QMainWindow`."""
        return self._workspace

    def event(self, e):
        """Scrap window events."""
        # When this window is in focus and selected, tell the application that
        # it's the active window
        if e.type() == QEvent.WindowActivate:
            self.window_activated.emit(self)

        return super(MainWindow, self).event(e)

    def _on_toggle_plugin_dock(self):
        """
        Show/hide the plugin dock depending on the state of the plugin
        action group.
        """
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

    def _on_plugin_dock_visbility_changed(self, visible):
        if not visible:
            for act in self._plugin_action_group.actions():
                act.setChecked(False)