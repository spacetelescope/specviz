import os
from collections import OrderedDict

import qtawesome as qta
from astropy.io import registry as io_registry
from qtpy import compat
from qtpy.QtCore import Qt, Signal, QEvent
from qtpy.QtWidgets import (QApplication, QWidget, QActionGroup,
                            QTabBar, QMainWindow, QToolButton, QSizePolicy)
from qtpy.uic import loadUi
from specutils import Spectrum1D

from . import resources
from .plotting import PlotWindow
from .smoothing import SmoothingDialog
from ..core.items import PlotDataItem
from ..core.models import DataListModel
from ..utils import UI_PATH
from ..utils.qt_utils import dict_to_menu


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
        self._name = "Untitled Workspace"

        # Load the ui file and attach it to this instance
        loadUi(os.path.join(UI_PATH, "workspace.ui"), self)

        # Add spacers to the main tool bar
        spacer = QWidget()
        spacer.setFixedSize(self.main_tool_bar.iconSize() * 2)
        self.main_tool_bar.insertWidget(self.load_data_action, spacer)

        spacer = QWidget()
        spacer.setFixedSize(self.main_tool_bar.iconSize() * 2)
        self.main_tool_bar.insertWidget(self.new_plot_action, spacer)

        spacer = QWidget()
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(1)
        spacer.setSizePolicy(size_policy)
        self.main_tool_bar.addWidget(spacer)

        # Update title
        self.setWindowTitle(self.name + " — SpecViz")

        # Setup workspace action connections
        self.new_workspace_action.triggered.connect(
            QApplication.instance().add_workspace)
        self.new_plot_action.triggered.connect(
            self._on_new_plot)

        # Setup data action connections
        self.load_data_action.triggered.connect(
            self._on_load_data)
        self.delete_data_action.triggered.connect(
            self._on_delete_data)

        # Setup operations menu
        operations_button = self.main_tool_bar.widgetForAction(self.operations_action)
        operations_button.setPopupMode(QToolButton.InstantPopup)

        operations_menu = dict_to_menu(self, OrderedDict([
            ('Smoothing', self._on_smoothing)
        ]))
        operations_button.setMenu(operations_menu)

        # Define a new data list model for this workspace
        self._model = DataListModel()

        # Set the styled item delegate on the model
        # self.list_view.setItemDelegate(DataItemDelegate(self))

        # When the current subwindow changes, mount that subwindow's proxy model
        self.mdi_area.subWindowActivated.connect(self._on_sub_window_activated)

        # Add an initially empty plot
        self.add_plot_window()

        # Load editor ui files
        self._model_editor = QWidget()
        loadUi(os.path.join(UI_PATH, "model_editor.ui"), self._model_editor)
        self._model_editor.add_model_button.setIcon(
            qta.icon('fa.plus'))
        self._model_editor.remove_model_button.setIcon(
            qta.icon('fa.minus'))

        # Hide the plugin dock initially
        self.plugin_dock.hide()

        self._statistics = QWidget()
        loadUi(os.path.join(UI_PATH, "statistics.ui"), self._statistics)

        # Setup plugin toolbar
        self._plugin_action_group = QActionGroup(self)
        self.model_editor_toggle.setActionGroup(self._plugin_action_group)
        self.statistics_toggle.setActionGroup(self._plugin_action_group)
        self.mask_editor_toggle.setActionGroup(self._plugin_action_group)

        # Setup plugin toolbar action actions
        self._plugin_action_group.triggered.connect(self._on_toggle_plugin_dock)
        self._last_toggled_action = None

        # Model editing
        from ..core.models import ModelFittingModel, ModelFittingProxyModel

        model_fitting_model = ModelFittingModel()
        model_fitting_proxy_model = ModelFittingProxyModel()
        model_fitting_proxy_model.setSourceModel(model_fitting_model)

        self._model_editor.model_tree_view.setModel(model_fitting_proxy_model)
        self._model_editor.model_tree_view.setHeaderHidden(True)
        self._model_editor.parameter_tree_view.setModel(model_fitting_model)

        def _set_root(idx):
            src_idx = model_fitting_proxy_model.mapToSource(idx)
            idx = src_idx.siblingAtColumn(1)
            self._model_editor.parameter_tree_view.setRootIndex(idx)

        self._model_editor.model_tree_view.selectionModel().currentChanged.connect(_set_root)

        # Attach individual loading of editors to their actions
        self.model_editor_toggle.triggered.connect(
            lambda: self._on_editor_triggered(self.model_editor_toggle.objectName()))
        self.statistics_toggle.triggered.connect(
            lambda: self._on_editor_triggered(self.statistics_toggle.objectName()))
        self.mask_editor_toggle.triggered.connect(
            lambda: self._on_editor_triggered(self.mask_editor_toggle.objectName()))

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
        else:
            self.menu_bar.show()
            self.list_view.show()
            self.main_tool_bar.show()
            self.main_tool_bar.show()
            self.mdi_area.findChild(QTabBar).show()

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
        self.list_view.selectionModel().currentChanged.connect(plot_window._on_current_item_changed)

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
        spec = Spectrum1D.read(file_path, format=file_loader)
        name = file_path.split('/')[-1].split('.')[0]
        data_item = self.model.add_data(spec, name=name)

        # print(self.proxy_model._items.keys())

        # if display:
        #     idx = data_item.index()
        #     plot_item = self.proxy_model.item_from_index(idx)
        #     plot_item.visible = True

        return data_item

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

    def _on_smoothing(self):
        """Launches smoothing UI"""
        return SmoothingDialog(self, parent=self)

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
