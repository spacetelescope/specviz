from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QApplication, QWidget, QMenu, QToolButton, QToolBar
from qtpy.QtCore import Signal
from functools import wraps

from ..widgets import resources


class Plugin:
    @property
    def workspace(self):
        """Returns the active workspace."""
        return QApplication.instance().current_workspace

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
        return self.workspace.current_plot_window

    @property
    def plot_windows(self):
        """Returns the currently selected plot window of the workspace."""
        return self.workspace.mdi_area.subWindowList()

    @property
    def plot_widget(self):
        """The plot widget of the currently active plot window."""
        return self.workspace.current_plot_window.plot_widget

    @property
    def plot_item(self):
        """Returns the currently selected plot item."""
        if self.workspace is not None:
            return self.workspace.current_item

    @property
    def plot_items(self):
        """Returns the currently selected plot item."""
        return self.proxy_model.items

    @property
    def selected_region(self):
        """Returns the currently active ROI on the plot."""
        return self.plot_window.plot_widget.selected_region

    @property
    def selected_region_bounds(self):
        """Returns the bounds of currently active ROI on the plot."""
        return self.plot_window.plot_widget.selected_region_bounds

    @property
    def data_item(self):
        """Returns the data item of the currently selected plot item."""
        if self.plot_item is not None:
            return self.plot_item.data_item

    @property
    def data_items(self):
        """Returns a list of all data items held in the data item model."""
        return self.model.items


class DecoratorRegistry:
    def __init__(self):
        self._registry = []

    @property
    def registry(self):
        return self._registry

    @staticmethod
    def get_action(parent, level=None):
        """
        Creates nested menu actions dependending on the user-created plugin
        decorator location values.
        """
        for action in parent.actions():
            if action.text() == level:
                if isinstance(parent, QToolBar):
                    button = parent.widgetForAction(action)
                    button.setPopupMode(QToolButton.InstantPopup)
                elif isinstance(parent, QMenu):
                    button = action

                if button.menu():
                    menu = button.menu()
                else:
                    menu = QMenu(parent)
                    button.setMenu(menu)

                return menu
        else:
            action = QAction(parent)
            action.setText(level)

            if isinstance(parent, QToolBar):
                parent.addAction(action)
                button = parent.widgetForAction(action)
                button.setPopupMode(QToolButton.InstantPopup)
            elif isinstance(parent, QMenu):
                parent.addAction(action)
                button = action

            menu = QMenu(parent)
            button.setMenu(menu)

            return menu


class PluginBarDecorator(DecoratorRegistry):
    def __call__(self, name, icon):
        def plugin_bar_decorator(cls):
            cls.wrapped = True
            cls.is_plugin_bar = True

            @wraps(cls)
            def cls_wrapper(*args, **kwargs):
                app = QApplication.instance()

                if app.current_workspace is None:
                    return

                plugin = cls()

                if plugin.workspace is not None:
                    plugin.workspace.plugin_tab_widget.addTab(
                        plugin, icon, name)

            self.registry.append(cls_wrapper)

            return cls_wrapper()
        return plugin_bar_decorator


class ToolBarDecorator(DecoratorRegistry):
    def __call__(self, name, icon=None, location=None):
        def tool_bar_decorator(func):
            func.wrapped = True
            func.is_main_tool = True

            @wraps(func)
            def func_wrapper(*args, **kwargs):
                app = QApplication.instance()

                if app.current_workspace is None:
                    return

                parent = app.current_workspace.main_tool_bar
                action = QAction(parent)
                action.setText(name)

                if icon is not None:
                    action.setIcon(icon)

                if location is not None:
                    for level in location.split('/'):
                        parent = self.get_action(parent, level)

                parent.addAction(action)
                action.triggered.connect(lambda: func(*args, **kwargs))

            self.registry.append(func_wrapper)

            return func_wrapper()
        return tool_bar_decorator


class PlotBarDecorator(DecoratorRegistry):
    def __call__(self, name, icon=None, location=None):
        def plot_bar_decorator(func):
            func.wrapped = True
            func.is_plot_tool = True

            @wraps(func)
            def func_wrapper(*args, **kwargs):
                app = QApplication.instance()

                if app.current_workspace is None:
                    return

                parent = app.current_workspace.current_plot_window.tool_bar
                action = QAction(parent)

                action.setText(name)

                if icon is not None:
                    action.setIcon(icon)

                if location is not None:
                    for level in location.split('/'):
                        parent = self.get_action(parent, level)

                before_action = [x for x in parent.actions()
                                 if x.isSeparator()].pop()
                parent.insertAction(before_action, action)
                action.triggered.connect(lambda: func(*args, **kwargs))

            self.registry.append(func_wrapper)

            return func_wrapper()
        return plot_bar_decorator


plugin_bar = PluginBarDecorator()
tool_bar = ToolBarDecorator()
plot_bar = PlotBarDecorator()