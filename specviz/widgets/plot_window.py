import os
import logging
import numpy as np
import pyqtgraph as pg
import qtawesome as qta
from astropy import units as u

from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog, QDialogButtonBox
from qtpy.uic import loadUi

from ..utils import UI_PATH

logging.basicConfig(level=logging.DEBUG, format="%(filename)s: %(levelname)8s %(message)s")
log = logging.getLogger('UnitChangeDialog')
log.setLevel(logging.WARNING)


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
            qta.icon('fa.exchange',
                     active='fa.legal',
                     color='black',
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

        # Load the ui dialog
        self.ui = loadUi(os.path.join(UI_PATH, "unit_change_dialog.ui"), self)

        # Load Units to be used in combobox
        self._units = [u.m, u.cm, u.mm, u.um, u.nm, u.AA]
        self._units_titles = list(u.long_names[0].title() for u in self._units) + ["Custom"]
        self.current_units = self._units_titles[0]

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the PyQt UI for this dialog."""
        self.ui.comboBox_units.addItems(self._units_titles)
        self.ui.line_custom.hide()
        self.ui.label_valid_units.hide()
        self.ui.label_convert.setText("Convert Units from {} to: ".format(self.current_units))

    def setup_connections(self):
        """Setup signal/slot connections for this dialog."""
        self.ui.comboBox_units.currentTextChanged.connect(self.on_combobox_change)
        self.ui.line_custom.textChanged.connect(self.on_line_custom_change)

        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.on_accepted)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.on_canceled)

    def on_combobox_change(self):
        """Called when the text of the unit combo box has changed."""
        if self.ui.comboBox_units.currentText() == "Custom":
            self.ui.line_custom.show()

            self.ui.label_valid_units.show()
            self.ui.label_valid_units.setText("Enter custom units")
            self.ui.label_valid_units.setStyleSheet('color: green')
        else:
            self.ui.line_custom.hide()
            self.ui.label_valid_units.hide()

    def on_line_custom_change(self):
        """Called when the text of the custom units textbox has changed."""
        if self.ui.line_custom.text() in ["", " "]:
            self.ui.label_valid_units.setText("Enter custom units")
            self.ui.label_valid_units.setStyleSheet('color: green')
            return

        try:
            u.Unit(self.ui.line_custom.text())
            self.ui.label_valid_units.setStyleSheet('color: green')
            self.ui.label_valid_units.setText("{} is Valid".format(self.ui.line_custom.text()))

        except Exception as e:
            log.debug(e)
            err = str(e)
            if "Did you mean " in err:
                similar_valid_units = err.split("Did you mean ")[1][:-1]
                self.ui.label_valid_units.setText("Invalid, try: {}".format(similar_valid_units))
            else:
                self.ui.label_valid_units.setText("Invalid")

            self.ui.label_valid_units.setStyleSheet('color: red')

    def on_accepted(self):
        """Called when the user clicks the "Ok" button of the dialog."""
        if self.ui.comboBox_units.currentText() == "Custom":
            try:
                u.Unit(self.ui.line_custom.text())
            except Exception as e:
                log.warning("DID NOT CHANGE UNITS. {}".format(e))
                self.close()

            self.current_units = self.line_custom.text()
        else:
            self.current_units = self.ui.comboBox_units.currentText()
        self.close()

    def on_canceled(self):
        """Called when the user clicks the "Cancel" button of the dialog."""
        self.close()
