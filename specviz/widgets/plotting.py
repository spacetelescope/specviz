import os
import numpy as np
import logging
import pyqtgraph as pg
import qtawesome as qta
from astropy import units as u

from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog, QDialogButtonBox
from qtpy.QtCore import Signal, QObject, Property
from qtpy.uic import loadUi

from ..core.models import PlotProxyModel
from ..utils import UI_PATH

logging.basicConfig(level=logging.DEBUG, format="%(filename)s: %(levelname)8s %(message)s")
log = logging.getLogger('UnitChangeDialog')
log.setLevel(logging.WARNING)


class PlotWindow(QMdiSubWindow):
    def __init__(self, model, *args, **kwargs):
        super(PlotWindow, self).__init__(*args, **kwargs)

        # The central widget of the sub window will be a main window so that it
        # can support having tab bars
        self._main_window = QMainWindow()
        self.setWidget(self._main_window)

        loadUi(os.path.join(UI_PATH, "plot_window.ui"), self._main_window)

        # The central widget of the main window widget will be the plot
        self._model = model
        self._plot_widget = PlotWidget(model=self._model)
        self._main_window.setCentralWidget(self._plot_widget)

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

        self.setup_connections()

    @property
    def plot_widget(self):
        return self._plot_widget

    def setup_connections(self):
        def change_color():
            model = self._model
            data_item = model.items[0]
            print("Changing color on", data_item.name)
            data_item.color = '#000000'

        self._main_window.plot_options_action.triggered.connect(change_color)
        self._main_window.change_unit_action.triggered.connect(self._on_change_unit)

    def _on_change_unit(self):
        unit_change = UnitChangeDialog()
        unit_change.exec_()


class PlotWidget(pg.PlotWidget):
    plot_added = Signal()
    plot_removed = Signal()

    def __init__(self, name=None, model=None, *args, **kwargs):
        super(PlotWidget, self).__init__(*args, **kwargs)

        self._name = name or "Untitled Plot"

        # Store the unit information for this plot. This is defined by the
        # first data set that gets plotted. All other data sets will attempt
        # to be converted to these units.
        self._data_unit = None
        self._spectral_axis_unit = None

        # Cache a reference to the model object that's attached to the parent
        self._proxy_model = PlotProxyModel(model)

        self.setup_connections()

    @property
    def name(self):
        return self._name

    @property
    def proxy_model(self):
        return self._proxy_model

    @property
    def data_unit(self):
        return self._data_unit

    @property
    def spectral_axis_unit(self):
        return self._spectral_axis_unit

    def setup_connections(self):
        # Listen for model events to add/remove items from the plot
        self._proxy_model.rowsInserted.connect(self.add_plot)
        self._proxy_model.rowsAboutToBeRemoved.connect(self.remove_plot)

    def add_plot(self, index, first, last):
        # Retrieve the data item from the model
        plot_data_item = self._proxy_model.data(index)

        self.addItem(plot_data_item)

        # Emit a plot added signal
        self.plot_added.emit()

    def remove_plot(self, index, first, last):
        # Retrieve the data item from the model
        plot_data_item = self._proxy_model.data(index)

        if plot_data_item is not None:
            # Remove plot data item from this plot
            self.removeItem(plot_data_item)

            # Emit a plot added signal
            self.plot_removed.emit()


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
                return False
            # If there are no units, just close the dialog and return False
            if self.ui.line_custom.text() in ["", " "]:
                log.warning("No custom units entered, units did not change")
                self.close()
                return False

            self.current_units = self.line_custom.text()
        else:
            self.current_units = self.ui.comboBox_units.currentText()
        self.close()
        return True

    def on_canceled(self):
        """Called when the user clicks the "Cancel" button of the dialog."""
        self.close()
