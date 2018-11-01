from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QApplication, QWidget, QMenu, QToolButton, QToolBar
from qtpy.QtCore import Signal
from functools import wraps
import inspect
import logging

from .hub import Hub


class DecoratorRegistry:
    def __init__(self, *args, **kwargs):
        self._registry = []

    @property
    def registry(self):
        return self._registry

    @staticmethod
    def get_action(parent, level=None):
        """
        Creates nested menu actions depending on the user-created plugin
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


class Plugin(DecoratorRegistry):
    @property
    def registry(self):
        return self._registry

    def __call__(self, name, priority=0):
        logging.info("Adding plugin '%s'.", name)

        def plugin_decorator(cls):
            cls.wrapped = True
            cls.type = None
            cls.priority = priority

            @wraps(cls)
            def cls_wrapper(workspace, filt=None, *args, **kwargs):
                if workspace is None:
                    return

                cls.hub = Hub(workspace)
                plugin = cls()

                workspace._plugins[name] = plugin

                # Call any internal tool or plot bar decorators
                members = inspect.getmembers(plugin, predicate=inspect.ismethod)

                for meth_name, meth in members:
                    if hasattr(meth, 'wrapped') and (filt is None or meth.plugin_type == filt):
                        meth(workspace)

                return plugin

            self._registry.append(cls_wrapper)

            return cls_wrapper
        return plugin_decorator

    def mount(self, workspace, filt=None):
        for plugin in sorted(self.registry, key=lambda x: -x.priority):
            plugin(workspace, filt=filt)

    def plugin_bar(self, name, icon, priority=0):
        def plugin_bar_decorator(cls):
            cls.wrapped = True
            cls.type = 'plugin_bar'
            cls.priority = priority

            @wraps(cls)
            def cls_wrapper(workspace, *args, **kwargs):
                if workspace is None:
                    return

                cls.hub = Hub(workspace)
                plugin = cls()

                workspace._plugin_bars[name] = plugin

                if workspace is not None:
                    # Check if this plugin already exists as a tab
                    for i in range(workspace.plugin_tab_widget.count()):
                        if workspace.plugin_tab_widget.tabText(i) == name:
                            plugin = workspace.plugin_tab_widget.widget(i)

                            # In the case where the plugin is already added to
                            # the plugin bar, we only want to re-add any
                            # internal plot bar plugins.
                            members = inspect.getmembers(
                                plugin, predicate=inspect.ismethod)
                            [meth(workspace) for meth_name, meth in members
                             if hasattr(meth, 'wrapped')
                             and meth.plugin_type == 'plot_bar']

                            break
                    else:
                        workspace.plugin_tab_widget.addTab(
                            plugin, icon, name)

                        # Call any internal tool or plot bar decorators. Since
                        # this is the first time this plugin is being added to
                        # the bar, make sure to include both plot and tool bar
                        # plugins.
                        members = inspect.getmembers(
                            plugin, predicate=inspect.ismethod)
                        [meth(workspace) for meth_name, meth in members
                         if hasattr(meth, 'wrapped')]

            self.registry.append(cls_wrapper)

            return cls_wrapper
        return plugin_bar_decorator

    def tool_bar(self, name, icon=None, location=None, priority=0):
        def tool_bar_decorator(func):
            func.wrapped = True
            func.plugin_type = 'tool_bar'
            func.priority = priority

            @wraps(func)
            def func_wrapper(plugin, workspace, *args, **kwargs):
                if workspace is None:
                    return

                parent = workspace.main_tool_bar
                action = QAction(parent)
                action.setText(name)

                if icon is not None:
                    action.setIcon(icon)

                if location is not None and isinstance(location, str):
                    for level in location.split('/'):
                        parent = self.get_action(parent, level)

                if isinstance(location, int):
                    parent.insertAction(parent.actions()[location], action)
                else:
                    parent.addAction(action)

                action.triggered.connect(lambda: func(plugin, *args, **kwargs))

            # self.registry.append(func_wrapper)

            return func_wrapper
        return tool_bar_decorator

    def plot_bar(self, name, icon=None, location=None, priority=0):
        def plot_bar_decorator(func):
            func.wrapped = True
            func.plugin_type = 'plot_bar'
            func.priority = priority

            @wraps(func)
            def func_wrapper(plugin, workspace, *args, **kwargs):
                if workspace is None:
                    return

                if workspace.current_plot_window is None:
                    return

                parent = workspace.current_plot_window.tool_bar
                action = QAction(parent)

                action.setText(name)

                if icon is not None:
                    action.setIcon(icon)

                if location is not None and isinstance(location, str):
                    for level in location.split('/'):
                        parent = self.get_action(parent, level)

                before_action = [x for x in parent.actions()
                                 if x.isSeparator()].pop()
                parent.insertAction(before_action, action)
                action.triggered.connect(lambda: func(plugin, *args, **kwargs))

            # self.registry.append(func_wrapper)

            return func_wrapper
        return plot_bar_decorator


plugin = Plugin()

