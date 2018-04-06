from abc import ABCMeta, abstractmethod, abstractproperty
import six
import os

from qtpy.QtCore import Qt, QRect
from qtpy.QtWidgets import (QDockWidget, QScrollArea, QFrame, QWidget, QMenu,
                            QAction, QWidgetAction, QToolButton)
from qtpy.QtGui import QIcon
from qtpy.uic import loadUi

from ..core.events import dispatch
from ..interfaces.registries import plugin_registry
from ..widgets.utils import UI_PATH


class PluginMeta(type):
    def __new__(cls, *args, **kwargs):
        cls = super(PluginMeta, cls).__new__(cls, *args, **kwargs)

        if cls.__name__ != "Plugin":
            plugin_registry.add(cls)

        return cls


class PluginMetaProxy(type(QDockWidget), PluginMeta): pass


@six.add_metaclass(PluginMetaProxy)
class Plugin(QDockWidget):
    """
    Base object for plugin infrastructure.
    """
    location = 'hidden'
    priority = 1

    def __init__(self, parent=None):
        super(Plugin, self).__init__(parent)
        # Initialize this plugin's actions list
        self._actions = []

        # Keep a reference to the active sub window
        self._active_window = None
        self._current_layer = None

        dispatch.setup(self)

        # GUI Setup
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        loadUi(os.path.join(UI_PATH, "plugin.ui"), self)

        self.setWindowTitle(self.name)

        self.setup_ui()
        self.setup_connections()

        self.contents.resize(self.contents.sizeHint())

    def _set_name(self, value):
        if isinstance(value, str):
            self.name = value
        else:
            raise TypeError("Inappropriate type for 'name' property.")

    def _get_name(self):
        return self.name

    name = abstractproperty(_set_name, _get_name)

    @abstractmethod
    def setup_ui(self):
        raise NotImplementedError()

    @abstractmethod
    def setup_connections(self):
        raise NotImplementedError()

    def _dict_to_menu(self, menu_dict, menu_widget=None):
        if menu_widget is None:
            menu_widget = QMenu()

        for k, v in menu_dict.items():
            if isinstance(v, dict):
                new_menu = menu_widget.addMenu(k)
                self._dict_to_menu(v, menu_widget=new_menu)
            else:
                act = QAction(k, menu_widget)

                if isinstance(v, list):
                    if v[0] == 'checkable':
                        v = v[1]
                        act.setCheckable(True)
                        act.setChecked(True)

                act.triggered.connect(v)
                menu_widget.addAction(act)

        return menu_widget

    def add_tool_bar_actions(self, icon_path, name="", category=None,
                             description="", priority=0, enabled=True,
                             callback=None, menu=None):
        icon = QIcon(icon_path)

        if menu is not None:
            tool_button = QToolButton()
            tool_button.setPopupMode(QToolButton.InstantPopup)

            menu_widget = self._dict_to_menu(menu)

            tool_button.setMenu(menu_widget)
            tool_button.setIcon(icon)
            tool_button.setText(name)
            tool_button.setStatusTip(description)
            tool_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

            item = QWidgetAction(self)
            item.setDefaultWidget(tool_button)
            item.setEnabled(enabled)
        else:
            item = QAction(self)
            item.triggered.connect(callback if callback is not None else
                                     lambda: None)
            item.setIcon(icon)
            item.setStatusTip(description)
            item.setEnabled(enabled)
            item.setText(name)

        self._actions.append(dict(action=item,
                                  category=(category, 0) if not isinstance(
                                      category, tuple) else category,
                                  priority=priority))

        return item

    @property
    def active_window(self):
        return self._active_window

    @property
    def current_layer(self):
        return self._current_layer

    @dispatch.register_listener("on_activated_window")
    def set_active_window(self, window):
        self._active_window = window

    @dispatch.register_listener("on_selected_layer")
    def set_active_layer(self, layer_item):
        if layer_item is not None:
            self._current_layer = layer_item.data(0, Qt.UserRole)
        else:
            self._current_layer = None
