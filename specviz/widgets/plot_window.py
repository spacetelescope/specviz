import os
import numpy as np
import pyqtgraph as pg
import qtawesome as qta
from astropy import units as u

from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog
from qtpy.uic import loadUi

from ..utils import UI_PATH


class UiPlotWindow(QMdiSubWindow):
    def __init__(self, *args, **kwargs):
        super(UiPlotWindow, self).__init__(*args, **kwargs)

        # Setup UI
        self._main_window = QMainWindow()
        loadUi(os.path.join(UI_PATH, "plot_window.ui"), self._main_window)

        self._plot_widget = pg.PlotWidget()

        self._main_window.setCentralWidget(self._plot_widget)

        self.setWidget(self._main_window)

        self.setup_connections()

        # Add the qtawesome icons to the plot-specific actions
        self._main_window.linear_region_action.setIcon(
            qta.icon('fa.compress',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.rectangular_region_action.setIcon(
            qta.icon('fa.square',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.plot_options_action.setIcon(
            qta.icon('fa.line-chart',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.export_plot_action.setIcon(
            qta.icon('fa.download',
                     active='fa.legal',
                     color='black',
                     color_active='orange'))

        self._main_window.change_unit_action.setIcon(
            qta.icon('fa.download',
                     active='fa.legal',
                     color='blue',
                     color_active='orange'))

    def setup_connections(self):
        self._main_window.change_unit_action.triggered.connect(self._on_change_unit)

    def _on_change_unit(self):
        unit_change = UnitChangeDialog()
        unit_change.exec_()


class PlotWindow(UiPlotWindow):
    def __init__(self, name=None, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)

        self._name = name or "Untitled Plot"

        # Add plot data from the data model
        self._plot_widget.plot(np.arange(100), np.random.sample(100))

    @property
    def name(self):
        return self._name


class UnitChangeDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(UnitChangeDialog, self).__init__(*args, **kwargs)

        self.ui = loadUi(os.path.join(UI_PATH, "unit_change_dialog.ui"), self)

        self._units = [u.m, u.cm, u.mm, u.um, u.nm, u.AA]
        self._units_titles = list(u.long_names[0].title() for u in self._units) + ["Custom"]
        self.ui.comboBox_2.addItems(self._units_titles)

        self.ui.comboBox_2.currentTextChanged.connect(self.current_text_changed)

        self.ui.lineEdit.hide()

    def current_text_changed(self):
        print(self.ui.comboBox_2.currentText())
        if self.ui.comboBox_2.currentText() == "Custom":
            self.ui.lineEdit.show()
        else:
            self.ui.lineEdit.hide()
