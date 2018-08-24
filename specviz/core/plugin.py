from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QApplication, QWidget

from ..widgets import resources


class Plugin(QWidget):
    name = "Custom Plugin"
    icon = QIcon(":/icons/012-file.svg")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = QApplication.instance()

        self._action = QAction(self.workspace.plugin_tool_bar)
        self._action.setText(self.name)
        self._action.setIcon(self.icon)
        self._action.setCheckable(True)

    @property
    def action(self):
        return self._action

    @property
    def workspace(self):
        """Returns the active workspace."""
        return self.app.current_workspace

    @property
    def model(self):
        """Returns the data item model of the active workspace."""
        return self.workspace.model

    @property
    def proxy_model(self):
        """Returns the proxy model of the active workspace."""
        return self.workspace.proxy_model

    @property
    def plot_window(self):
        """Returns the currently selected plot window of the workspace."""
        return self.workspace.plot_window

    @property
    def plot_item(self):
        """Returns the currently selected plot item."""
        return self.workspace.current_item

    @property
    def data_item(self):
        """Returns the data item of the currently selected plot item."""
        return self.plot_item.data_item

    @property
    def data_items(self):
        """Returns a list of all data items held in the data item model."""
        return self.model.items

    def add_to_plugin_bar(self):

        # Add the action to the toolbar
        self.workspace.plugin_tool_bar.addAction(self.action)

        # Add the plugin action to the plugin bar toggle group
        self.action.setActionGroup(self.workspace.plugin_action_group)

        # When the action is clicked, ensure that the connect to the dock
        # widget is made.
        self.action.triggered.connect(lambda: self.set_plugin_dock())

    def set_plugin_dock(self):
        self.workspace.plugin_dock.setWidget(self)