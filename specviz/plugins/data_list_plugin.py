"""
Plugin to manage the loaded data
"""
import os

import astropy.io.registry as io_registry
from qtpy.QtWidgets import (QToolButton, QHBoxLayout,
                            QSizePolicy, QListWidget, QAbstractItemView,
                            QListWidgetItem, QVBoxLayout)
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QIcon
from qtpy import compat

from ..core.comms import dispatch, DispatchHandle
from ..widgets.utils import ICON_PATH
from ..core.data import Spectrum1DRef
from ..core.threads import FileLoadThread
from ..widgets.plugin import Plugin


class DataListPlugin(Plugin):
    """
    UI plugin to manage the data.
    """
    name = "Data List"
    location = "left"

    def __init__(self, *args, **kwargs):
        super(DataListPlugin, self).__init__(*args, **kwargs)

        self._loader_threads = []

        # Store the most recent file selector
        self._file_filter = None
        self._directory = ""

        # Add tool tray buttons
        self.button_open_data = self.add_tool_bar_actions(
            name="Open",
            description='Open data file',
            icon_path=os.path.join(ICON_PATH, "Open Folder-48.png"),
            category=('Loaders', 5),
            priority=1,
            callback=lambda: dispatch.on_file_open.emit())

    def setup_ui(self):
        UiDataListPlugin(self)

    def setup_connections(self):
        # Enable/disable buttons depending on selection
        self.list_widget_data_list.itemSelectionChanged.connect(
            self.toggle_buttons)

        # Connect the create new sub window button
        self.button_create_sub_window.clicked.connect(
            lambda: dispatch.on_add_window.emit(data=self.current_data))

        # Connect the add to current plot window button
        self.button_add_to_sub_window.clicked.connect(
            lambda: dispatch.on_add_to_window.emit(
                data=self.current_data,
                window=self.active_window))

        # When the data list delete button is pressed
        self.button_remove_data.clicked.connect(
            lambda: self.remove_data_item())

        self.button_apply_model.clicked.connect(
            self.apply_model)

    def _file_load_result(self, data, thread, auto_open):
        self._data_loaded(data, auto_open=auto_open)
        self._loader_threads.remove(thread)

    @DispatchHandle.register_listener("on_add_data")
    def _data_loaded(self, data, auto_open=True):
        dispatch.on_added_data.emit(data=data)

        # Open the data automatically
        if auto_open:
            dispatch.on_add_window.emit(data=data)

    def apply_model(self):
        for data in self.get_selected_data():
            dispatch.on_paste_model.emit(data=data)

    @property
    def current_data(self):
        """
        Returns the currently selected data object from the data list widget.

        Returns
        -------
        data : specutils.core.generic.Spectrum1DRef
            The `Data` object of the currently selected row.
        """
        data_item = self.list_widget_data_list.currentItem()

        if data_item is not None:
            data = data_item.data(Qt.UserRole)
            return data

    @property
    def current_data_item(self):
        return self.list_widget_data_list.currentItem()

    @DispatchHandle.register_listener("on_file_open")
    def open_file(self, file_name=None):
        """
        Creates a :code:`specutils.core.generic.Spectrum1DRef` object from the `Qt`
        open file dialog, and adds it to the data item list in the UI.
        """
        if file_name is None:
            file_name, selected_filter = self.open_file_dialog()

            self.read_file(file_name, file_filter=selected_filter)

    def open_file_dialog(self):
        """
        Given a list of filters, prompts the user to select an existing file
        and returns the file path and filter.

        Returns
        -------
        file_name : str
            Path to the selected file.
        selected_filter : str
            The chosen filter (this indicates which custom loader from the
            registry to use).
        """

        filters = ["Auto (*)"] + [x for x in
                                  io_registry.get_formats(
                                      Spectrum1DRef)['Format']]

        file_names, self._file_filter = compat.getopenfilenames(basedir=self._directory,
                                                                filters=";;".join(filters),
                                                                selectedfilter=self._file_filter)

        if len(file_names) == 0:
            return None, None

        self._directory = file_names[0]

        return file_names[0], self._file_filter

    @DispatchHandle.register_listener("on_file_read")
    def read_file(self, file_name, file_filter=None, auto_open=True):
        file_load_thread = FileLoadThread()

        file_load_thread.status.connect(
            dispatch.on_status_message.emit)

        file_load_thread.result.connect(
            lambda d, t=file_load_thread: self._file_load_result(d, t, auto_open))

        self._loader_threads.append(file_load_thread)

        file_load_thread(file_name, file_filter)
        file_load_thread.start()

    @DispatchHandle.register_listener("on_added_data")
    def add_data_item(self, data):
        """
        Adds a `Data` object to the loaded data list widget.

        Parameters
        ----------
        data : specutils.core.generic.Spectrum1DRef
            The `Data` object to add to the list widget.
        """
        new_item = QListWidgetItem(data.name, self.list_widget_data_list)
        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)

        new_item.setData(Qt.UserRole, data)

        self.list_widget_data_list.setCurrentItem(new_item)

    @DispatchHandle.register_listener("on_remove_data")
    def remove_data_item(self, data=None):
        if data is None:
            data = self.current_data

        data_item = self.get_data_item(data)

        self.list_widget_data_list.takeItem(
            self.list_widget_data_list.row(data_item))

        dispatch.on_removed_data.emit(data=self.current_data)

    @DispatchHandle.register_listener("on_remove_all_data")
    def remove_all_data(self):
        print('*' * 100, self.list_widget_data_list.count())
        for i in range(self.list_widget_data_list.count()):
            item = self.list_widget_data_list.takeItem(i - 1)
            print(i)
            item.deleteLayer()

    def get_data_item(self, data):
        for i in range(self.list_widget_data_list.count()):
            data_item = self.list_widget_data_list.item(i)

            if data_item.data(Qt.UserRole) == data:
                return data_item

    def get_selected_data(self):
        selected_data = []

        for data_item in self.list_widget_data_list.selectedItems():
            data = data_item.data(Qt.UserRole)
            selected_data.append(data)

        return selected_data

    def toggle_buttons(self):
        if self.current_data_item is not None:
            self.button_remove_data.setEnabled(True)
            self.button_create_sub_window.setEnabled(True)
            self.button_apply_model.setEnabled(True)
            self.button_add_to_sub_window.setEnabled(True)
        else:
            self.button_remove_data.setEnabled(False)
            self.button_create_sub_window.setEnabled(False)
            self.button_apply_model.setEnabled(False)
            self.button_add_to_sub_window.setEnabled(False)


class UiDataListPlugin:
    def __init__(self, plugin):
        plugin.layout_vertical = QVBoxLayout()
        plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)
        plugin.layout_vertical.setSpacing(6)

        plugin.contents.setLayout(plugin.layout_vertical)
        plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)

        # List widget for the data sets
        plugin.list_widget_data_list = QListWidget(plugin)
        plugin.list_widget_data_list.setMinimumHeight(50)
        plugin.list_widget_data_list.setSizePolicy(QSizePolicy.Preferred,
                                                   QSizePolicy.Ignored)

        # Allow for multiple selections
        plugin.list_widget_data_list.setSelectionMode(
            QAbstractItemView.ExtendedSelection)

        plugin.layout_vertical.addWidget(plugin.list_widget_data_list)

        plugin.layout_horizontal = QHBoxLayout()

        plugin.button_create_sub_window = QToolButton(plugin)
        plugin.button_create_sub_window.setIcon(QIcon(os.path.join(
            ICON_PATH, "Open in Browser-50.png")))
        plugin.button_create_sub_window.setIconSize(QSize(25, 25))
        plugin.button_create_sub_window.setMinimumSize(QSize(35, 35))
        plugin.button_create_sub_window.setEnabled(False)

        plugin.button_add_to_sub_window = QToolButton(plugin)
        plugin.button_add_to_sub_window.setIcon(QIcon(os.path.join(
            ICON_PATH, "Change Theme-50.png")))
        plugin.button_add_to_sub_window.setIconSize(QSize(25, 25))
        plugin.button_add_to_sub_window.setMinimumSize(QSize(35, 35))
        plugin.button_add_to_sub_window.setEnabled(False)

        plugin.button_apply_model = QToolButton(plugin)
        plugin.button_apply_model.setIcon(QIcon(os.path.join(
            ICON_PATH, "Paste-96.png")))
        plugin.button_apply_model.setIconSize(QSize(25, 25))
        plugin.button_apply_model.setMinimumSize(QSize(35, 35))
        plugin.button_apply_model.setEnabled(False)

        plugin.button_remove_data = QToolButton(plugin)
        plugin.button_remove_data.setIcon(QIcon(os.path.join(
            ICON_PATH, "Delete-48.png")))
        plugin.button_remove_data.setEnabled(False)
        plugin.button_remove_data.setIconSize(QSize(25, 25))
        plugin.button_remove_data.setMinimumSize(QSize(35, 35))

        plugin.layout_horizontal.addWidget(plugin.button_create_sub_window)
        plugin.layout_horizontal.addWidget(plugin.button_add_to_sub_window)
        plugin.layout_horizontal.addWidget(plugin.button_apply_model)
        plugin.layout_horizontal.addStretch()
        plugin.layout_horizontal.addWidget(plugin.button_remove_data)

        plugin.layout_vertical.addLayout(plugin.layout_horizontal)



