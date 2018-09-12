from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QAction, QApplication, QWidget, QMenu, QToolButton, QToolBar
from functools import wraps

from ..widgets import resources


class Plugin:
    def __init__(self, filt=None):
        self._app = QApplication.instance()
        # For each decorated method in the plugin, call it in order to have
        # the decorator apply the behavior in the UI.
        method_list = [func for func in dir(self)
                       if hasattr(self, func)
                       and callable(getattr(self, func))
                       and not func.startswith("__")
                       and hasattr(getattr(self, func), 'wrapped')
                       and (filt is None or hasattr(getattr(self, func), filt))]

        [getattr(self, meth)() for meth in method_list]

    # def __call__(self, cls):
    #     class CustomPlugin(cls):
    #         def __getattribute__(self, attr):
    #             pass

    @property
    def workspace(self):
        """Returns the active workspace."""
        return self._app.current_workspace

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

    @staticmethod
    def plugin_bar(name, icon):
        def plugin_bar_decorator(func):
            func.wrapped = True

            @wraps(func)
            def func_wrapper(self, *args, **kwargs):
                self._action = QAction(self.workspace.plugin_tool_bar)
                self._action.setText(name)

                if icon is not None:
                    self._action.setIcon(icon)

                self._action.setCheckable(True)

                # Add the action to the toolbar
                self.workspace.plugin_tool_bar.addAction(self._action)

                # Add the plugin action to the plugin bar toggle group
                self._action.setActionGroup(self.workspace.plugin_action_group)

                # When the action is clicked, ensure that the connect to the
                # dock widget is made.
                self._action.triggered.connect(lambda: func(self, *args, **kwargs))

            return func_wrapper
        return plugin_bar_decorator

    @staticmethod
    def tool_bar(name, icon=None, location=None):
        def tool_bar_decorator(func):
            func.wrapped = True
            func.is_main_tool = True

            @wraps(func)
            def func_wrapper(self, *args, **kwargs):
                self._action = QAction(self.workspace.main_tool_bar)
                self._action.setText(name)

                if icon is not None:
                    self._action.setIcon(icon)

                parent = self.workspace.main_tool_bar

                if location is not None:
                    for level in location.split('/'):
                        parent = get_action(parent, level)

                parent.addAction(self._action)
                self._action.triggered.connect(lambda: func(self, *args, **kwargs))

            return func_wrapper
        return tool_bar_decorator

    @staticmethod
    def plot_bar(name, icon=None, location=None):
        def plot_bar_decorator(func):
            func.wrapped = True
            func.is_plot_tool = True

            @wraps(func)
            def func_wrapper(self, *args, **kwargs):
                self._action = QAction(self.plot_window.tool_bar)
                self._action.setText(name)

                if icon is not None:
                    self._action.setIcon(icon)

                parent = self.plot_window.tool_bar

                if location is not None:
                    for level in location.split('/'):
                        parent = get_action(parent, level)

                parent.addAction(self._action)
                self._action.triggered.connect(lambda: func(self, *args, **kwargs))

            return func_wrapper
        return plot_bar_decorator


def get_action(parent, level=None):
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