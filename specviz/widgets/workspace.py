import logging
import os
import sys
from collections import OrderedDict

from astropy.io import registry as io_registry
from qtpy import compat
from qtpy.QtCore import QEvent, Qt, Signal
from qtpy.QtWidgets import (QActionGroup, QApplication, QMainWindow, QMenu,
                            QMessageBox, QSizePolicy, QTabBar, QToolButton,
                            QWidget)
from qtpy.uic import loadUi
from specutils import Spectrum1D

from ..core.items import PlotDataItem
from ..core.models import DataListModel
from ..core.plugin import Plugin
from ..utils import UI_PATH
from ..utils.qt_utils import dict_to_menu
from .plotting import PlotWindow


class Workspace(QMainWindow):
    """
    A widget representing the primary interaction area for a given workspace.
    This includes the :class:`~qtpy.QtWidgets.QListView`, and the
    :class:`~qtpy.QtWigets.QMdiArea` widgets, and associated model information.

    Signals
    -------
    window_activated : :class:`~qtpy.QtWidgets.QMainWindow`
        Fired when a particular `QMainWindow` is activated.
    """
    window_activated = Signal(QMainWindow)
    current_item_changed = Signal(PlotDataItem)

    def __init__(self, *args, **kwargs):
        super(Workspace, self).__init__(*args, **kwargs)
        # Retain a reference to the application
        self._app = QApplication.instance()

        self._name = "Untitled Workspace"

        # Load the ui file and attach it to this instance
        loadUi(os.path.join(UI_PATH, "workspace.ui"), self)

        # Add spacers to the main tool bar
        # spacer = QWidget()
        # spacer.setFixedSize(self.main_tool_bar.iconSize() * 2)
        # # self.main_tool_bar.insertWidget(self.load_data_action, spacer)

        # spacer = QWidget()
        # spacer.setFixedSize(self.main_tool_bar.iconSize() * 2)
        # self.main_tool_bar.insertWidget(self.new_plot_action, spacer)

        # spacer = QWidget()
        # size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # size_policy.setHorizontalStretch(1)
        # spacer.setSizePolicy(size_policy)
        # self.main_tool_bar.addWidget(spacer)

        # Update title
        self.setWindowTitle(self.name + " — SpecViz")

        # Setup workspace action connections
        self.new_workspace_action.triggered.connect(
            self._on_add_workspace)
        self.new_plot_action.triggered.connect(
            self._on_new_plot)

        # Setup data action connections
        self.load_data_action.triggered.connect(
            self._on_load_data)
        self.delete_data_action.triggered.connect(
            self._on_delete_data)

        # Setup operations menu
        self.operations_button = self.main_tool_bar.widgetForAction(self.operations_action)
        self.operations_button.setPopupMode(QToolButton.InstantPopup)

        self.operations_menu = QMenu(self.operations_button)
        self.operations_button.setMenu(self.operations_menu)

        # Define a new data list model for this workspace
        self._model = DataListModel()

        # Set the styled item delegate on the model
        # self.list_view.setItemDelegate(DataItemDelegate(self))

        # When the current subwindow changes, mount that subwindow's proxy model
        self.mdi_area.subWindowActivated.connect(self._on_sub_window_activated)

        # Add an initially empty plot
        self.add_plot_window()

        # Setup plugin toolbar
        self.plugin_action_group = QActionGroup(self)

        # Setup plugin toolbar action actions
        self.plugin_action_group.triggered.connect(self._on_toggle_plugin_dock)
        self._last_toggled_action = None

    @property
    def name(self):
        """The name of this workspace."""
        return self._name

    @property
    def model(self):
        """
        The data model for this workspace.

        .. note:: there is always at most one model per workspace.
        """
        return self._model

    @property
    def proxy_model(self):
        return self.current_plot_window.proxy_model

    @property
    def current_plot_window(self):
        """
        Get the current active plot window tab.
        """
        return self.mdi_area.currentSubWindow() or self.mdi_area.subWindowList()[0]

    def remove_current_window(self):
        self.mdi_area.removeSubWindow(self.current_plot_window)

    @property
    def current_item(self):
        """
        Get the currently selected :class:`~specviz.core.items.PlotDataItem`.
        """
        idx = self.list_view.currentIndex()
        item = self.proxy_model.data(idx, role=Qt.UserRole)

        return item

    def _on_add_workspace(self):
        workspace = self._app.add_workspace()
        self._app.current_workspace = workspace

    def set_embeded(self, embed):
        """
        Toggles the visibility of certain parts of the ui to make it more
        amenable to being embeded in other applications.
        """
        if embed:
            self.menu_bar.hide()
            self.list_view.hide()
            self.main_tool_bar.hide()
            self.main_tool_bar.hide()
            self.mdi_area.findChild(QTabBar).hide()

    def event(self, e):
        """Scrap window events."""
        # When this window is in focus and selected, tell the application that
        # it's the active window
        if e.type() == QEvent.WindowActivate:
            self.window_activated.emit(self)

        return super().event(e)

    def add_plot_window(self):
        """
        Creates a new plot widget sub window and adds it to the workspace.
        """
        plot_window = PlotWindow(model=self.model, parent=self.mdi_area)
        self.list_view.setModel(plot_window.plot_widget.proxy_model)

        plot_window.setWindowTitle(plot_window._plot_widget.title)
        plot_window.setAttribute(Qt.WA_DeleteOnClose)

        self.mdi_area.addSubWindow(plot_window)
        plot_window.showMaximized()

        self.mdi_area.subWindowActivated.emit(plot_window)

        # Subscribe this new plot window to list view item selection events
        self.list_view.selectionModel().currentChanged.connect(
            plot_window._on_current_item_changed)

        # Load plot tool bar plugins
        for sub_cls in Plugin.__subclasses__():
            sub_cls(filt='is_plot_tool')

    def _on_sub_window_activated(self, window):
        if window is None:
            return

        # Disconnect all plot widgets from the core model's item changed event
        for sub_window in self.mdi_area.subWindowList():
            try:
                self._model.itemChanged.disconnect(
                    sub_window.plot_widget.on_item_changed)
            except TypeError:
                pass

        self.list_view.setModel(window.proxy_model)

        # Connect the current window's plot widget to the item changed event
        self.model.itemChanged.connect(window.plot_widget.on_item_changed)

        # Re-evaluate plot unit compatibilities
        window.plot_widget.check_plot_compatibility()

    def _on_toggle_visibility(self, state):
        idx = self.list_view.currentIndex()
        item = self.proxy_model.data(idx, role=Qt.UserRole)
        item.visible = state

        self.proxy_model.dataChanged.emit(idx, idx)

    def _on_new_plot(self):
        """
        Listens for UI input and creates a new
        :class:`~specviz.widgets.plotting.PlotWindow`.
        """
        self.add_plot_window()

    def _on_load_data(self):
        """
        When the user loads a data file, this method is triggered. It provides
        a file open dialog and from the dialog attempts to create a new
        :class:`~specutils.Spectrum1D` object and thereafter adds it to the
        data model.
        """
        filters = [x + " (*)" for x in io_registry.get_formats(Spectrum1D)['Format']]

        file_path, fmt = compat.getopenfilename(parent=self,
                                                caption="Load spectral data file",
                                                filters=";;".join(filters))

        if not file_path:
            return

        self.load_data(file_path, file_loader=fmt.split()[0])

    def load_data(self, file_path, file_loader, display=False):
        """
        Load spectral data given file path and loader.

        Parameters
        ----------
        file_path : str
            Path to location of the spectrum file.
        file_loader : str
            Format specified for the astropy io interface.
        display : bool
            Automatically add the loaded spectral data to the plot.

        Returns
        -------
        : :class:`~specviz.core.items.DataItem`
            The `DataItem` instance that has been added to the internal model.
        """
        try:
            spec = Spectrum1D.read(file_path, format=file_loader)
            name = file_path.split('/')[-1].split('.')[0]
            data_item = self.model.add_data(spec, name=name)

            return data_item
        except:
            message_box = QMessageBox()
            message_box.setText("Error loading data set.")
            message_box.setIcon(QMessageBox.Critical)
            message_box.setInformativeText(
                "{}\n{}".format(
                    sys.exc_info()[0], sys.exc_info()[1])
            )

            message_box.exec()

    def _on_delete_data(self):
        """
        Listens for data deletion events from the
        :class:`~specviz.widgets.main_window.MainWindow` and deletes the
        corresponding data item from the model.
        """
        proxy_idx = self.list_view.currentIndex()
        model_idx = self.proxy_model.mapToSource(proxy_idx)

        # Ensure that the plots get removed from all plot windows
        for sub_window in self.mdi_area.subWindowList():
            proxy_idx = sub_window.proxy_model.mapFromSource(model_idx)
            sub_window.plot_widget.remove_plot(index=proxy_idx)

        self.model.removeRow(model_idx.row())

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

    def on_plugin_action_triggered(self, object_name):
        if object_name == 'model_editor_toggle':
            self.plugin_dock.setWidget(self._model_editor)
        if object_name == 'statistics_toggle':
            self.plugin_dock.setWidget(self._statistics)
