from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QApplication, QWidget, QMenu, QToolButton, QToolBar
from qtpy.QtCore import Signal
from functools import wraps
import inspect
import logging

from .hub import Hub

__all__ = ['DecoratorRegistry', 'Plugin', 'plugin']


class DecoratorRegistry:
    """
    Base class for any decorator-based registry.
    """
    def __init__(self, *args, **kwargs):
        self._registry = []

    @property
    def registry(self):
        """
        Returns the list of registered decorators
        """
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
    """
    Decorator for plugin classes.

    For example, to decorate a specific plugin class as well define a
    tool bar plugin, you would do::

        @plugin("Custom Dialog")
        class MyPlyginDialog(QDialog):

            @plugin.tool_bar("Open Custom Dialog", icon=...)
            def open_dialog(self):
    """

    def __call__(self, name, priority=0):
        """
        Wraps the class and adds the decorated class to the registry.

        Parameters
        ----------
        name : str
            Name of plugin.
        priority : int
            The priority of when this plugin is loaded. Lower == sooner.

        Returns
        -------
        plugin_decorator : func
            The function to wrap the decorated class.
        """

        logging.info("Adding plugin '%s'.", name)

        def plugin_decorator(cls):
            """
            This is the actual decorator that gets returned when
            ``plugin(...)`` is called.
            """

            cls.wrapped = True
            cls.type = None
            cls.priority = priority

            @wraps(cls)
            def cls_wrapper(workspace, filt=None, *args, **kwargs):
                """
                Wrapper function that, when called, causes the plugin to be
                loaded into a specific workspace.
                """

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
        """
        Load all the plugins in the registry into the specified workspace.

        Parameters
        ----------
        workspace : `~specviz.widgets.workspace.Workspace`
            The workspace to load the plugins in.
        filt : {`None`, 'tool_bar', 'plot_bar'}, optional
            The type of plugin to load. If not specified, all plugins are
            loaded.
        """
        for plugin in sorted(self.registry, key=lambda x: -x.priority):
            plugin(workspace, filt=filt)

    def plugin_bar(self, name, icon, priority=0):
        """
        Generate a decorator for a callback method that can be triggered by a
        tab on the right of the window.

        Parameters
        ----------
        name : str
            The name of the tab
        icon : `~PyQt5.QtGui.QIcon`, optional
            The icon for the tab
        priority : int, optional
            The priority to use to load in the plugins - a higher value means
            the plugin will be loaded sooner.
        """

        def plugin_bar_decorator(cls):
            """
            This is the actual decorator that gets returned when
            ``plugin.plugin_bar(...)`` is called.
            """

            cls.wrapped = True
            cls.type = 'plugin_bar'
            cls.priority = priority

            @wraps(cls)
            def cls_wrapper(workspace, *args, **kwargs):
                """
                Wrapper function that, when called, causes the plugin to be
                loaded into a specific workspace.
                """
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
        """
        Generate a decorator for a callback method that can be triggered by a
        button in the application tool bar.

        Parameters
        ----------
        name : str
            The name of the tool to add
        icon : `~PyQt5.QtGui.QIcon`
            The icon for the tool
        location : int
            If specified, can be used to customize the position of the icon in
            the tool bar.
        priority : int, optional
            The priority to use to load in the plugins - a higher value means
            the plugin will be loaded sooner.
        """

        def tool_bar_decorator(func):
            """
            This is the actual decorator that gets returned when
            ``plugin.tool_bar(...)`` is called.
            """

            func.wrapped = True
            func.plugin_type = 'tool_bar'
            func.priority = priority

            @wraps(func)
            def func_wrapper(plugin, workspace, *args, **kwargs):
                """
                Wrapper function that, when called, causes the plugin to be
                loaded into a specific workspace.
                """

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
        """
        Generate a decorator for a callback method that can be triggered by a
        button in the plot tool bar.

        Parameters
        ----------
        name : str
            The name of the tool to add
        icon : `~PyQt5.QtGui.QIcon`
            The icon for the tool
        location : int
            If specified, can be used to customize the position of the icon in
            the tool bar.
        priority : int, optional
            The priority to use to load in the plugins - a higher value means
            the plugin will be loaded sooner.
        """

        def plot_bar_decorator(func):
            """
            This is the actual decorator that gets returned when
            ``plugin.plot_bar(...)`` is called.
            """

            func.wrapped = True
            func.plugin_type = 'plot_bar'
            func.priority = priority

            @wraps(func)
            def func_wrapper(plugin, workspace, *args, **kwargs):
                """
                Wrapper function that, when called, causes the plugin to be
                loaded into a specific workspace.
                """

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
                                 if x.isSeparator()].pop(-2)
                parent.insertAction(before_action, action)
                action.triggered.connect(lambda: func(plugin, *args, **kwargs))

            # self.registry.append(func_wrapper)

            return func_wrapper
        return plot_bar_decorator


plugin = Plugin()
