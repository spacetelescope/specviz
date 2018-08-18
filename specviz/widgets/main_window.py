import os
from collections import OrderedDict

from qtpy.QtCore import QCoreApplication, QEvent, Signal, Qt
from qtpy.QtWidgets import (QActionGroup, QApplication, QMainWindow, QTabBar,
                            QSizePolicy, QWidget, QMenu, QAction, QToolButton)
from qtpy.uic import loadUi
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtSvg import QSvgRenderer
import qtawesome as qta

from . import resources
from ..core.hub import Hub
from ..utils import UI_PATH
from ..utils.qt_utils import dict_to_menu
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

        # Load editor ui files
        self._model_editor = QWidget()
        loadUi(os.path.join(UI_PATH, "model_editor.ui"), self._model_editor)
        self._model_editor.add_model_button.setIcon(
            qta.icon('fa.plus'))
        self._model_editor.remove_model_button.setIcon(
            qta.icon('fa.minus'))

        self._statistics = QWidget()
        loadUi(os.path.join(UI_PATH, "statistics.ui"), self._statistics)

        # Add spacers to the main tool bar
        spacer = QWidget()
        spacer.setFixedSize(self.tool_bar.iconSize() * 2)
        self.tool_bar.insertWidget(self.load_data_action, spacer)

        spacer = QWidget()
        spacer.setFixedSize(self.tool_bar.iconSize() * 2)
        self.tool_bar.insertWidget(self.new_plot_action, spacer)

        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
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

        # Setup operations menu
        operations_button = self.tool_bar.widgetForAction(self.operations_action)
        operations_button.setPopupMode(QToolButton.InstantPopup)

        operations_menu = dict_to_menu(self, OrderedDict([
            ('Smoothing', self.workspace._on_smoothing)
        ]))
        operations_button.setMenu(operations_menu)

        # Setup plugin toolbar action actions
        self._plugin_action_group.triggered.connect(self._on_toggle_plugin_dock)
        self._last_toggled_action = None

        # Attach individual loading of editors to their actions
        self.model_editor_toggle.triggered.connect(
            lambda: self._on_editor_triggered(self.model_editor_toggle.objectName()))
        self.statistics_toggle.triggered.connect(
            lambda: self._on_editor_triggered(self.statistics_toggle.objectName()))
        self.mask_editor_toggle.triggered.connect(
            lambda: self._on_editor_triggered(self.mask_editor_toggle.objectName()))

    @property
    def workspace(self):
        """Return the workspace widget within this `QMainWindow`."""
        return self._workspace

    def set_embeded(self, embed):
        """
        Toggles the visibility of certain parts of the ui to make it more
        amenable to being embeded in other applications.
        """
        if embed:
            self.menu_bar.hide()
            self.workspace.list_view.hide()
            self.tool_bar.hide()
            self.plugin_tool_bar.hide()
            self.workspace.mdi_area.findChild(QTabBar).hide()
        else:
            self.menu_bar.show()
            self.workspace.list_view.show()
            self.tool_bar.show()
            self.plugin_tool_bar.show()
            self.workspace.mdi_area.findChild(QTabBar).show()

    def event(self, e):
        """Scrap window events."""
        # When this window is in focus and selected, tell the application that
        # it's the active window
        if e.type() == QEvent.WindowActivate:
            self.window_activated.emit(self)

        return super(MainWindow, self).event(e)

    def _on_toggle_plugin_dock(self, action):
        """
        Show/hide the plugin dock depending on the state of the plugin
        action group.
        """
        if action != self._last_toggled_action:
            self.plugin_dock.show()
            self.plugin_dock.setWindowTitle(action.text())
            self._last_toggled_action = action
        else:
            action.setChecked(False)
            self.plugin_dock.hide()
            self._last_toggled_action = None

    def _on_editor_triggered(self, object_name):
        if object_name == 'model_editor_toggle':
            self.plugin_dock.setWidget(self._model_editor)
        if object_name == 'statistics_toggle':
            self.plugin_dock.setWidget(self._statistics)
