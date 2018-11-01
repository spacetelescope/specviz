import logging
import os

import astropy.units as u
import numpy as np
from qtpy.QtWidgets import (QAction, QColorDialog, QDialog, QDialogButtonBox,
                            QListWidget, QMainWindow, QMdiSubWindow, QMenu,
                            QMessageBox, QSizePolicy, QToolButton, QWidget,
                            QWidgetAction)
from qtpy.QtGui import QIcon
from qtpy.uic import loadUi

from ...core.plugin import plugin
from ...core.hub import Hub

np.seterr(divide='ignore', invalid='ignore')
logging.basicConfig(level=logging.DEBUG, format="%(filename)s: %(levelname)8s %(message)s")
log = logging.getLogger('UnitChangeDialog')
log.setLevel(logging.WARNING)


@plugin("Unit Change Plugin")
class UnitChangeDialog(QDialog):
    """
    A dialog box that allows the user to change units
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load the ui dialog
        self.ui = loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "unit_change_dialog.ui")), self)

    def exec_(self):
        # If there is no plot item, don't even try to process unit info
        if self.hub.plot_item is None or len(self.hub.visible_plot_items) == 0:
            message_box = QMessageBox()
            message_box.setText("No item plotted, cannot parse unit information.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "There is currently no items plotted. Please plot an item "
                "before changing unit.")

            message_box.exec_()
            return

        # Prevents duplicate units from showing up each time this is executed
        self.ui.comboBox_units.clear()
        self.ui.comboBox_spectral.clear()

        # If the units in PlotWidget are not set, do not allow the user to click the OK button
        if not (self.hub.plot_widget.data_unit
                and self.hub.plot_widget.spectral_axis_unit):
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        # Gets all possible conversions from current spectral_axis_unit
        self._spectral_axis_unit_equivalencies = u.Unit(
            self.hub.data_item.spectral_axis[0]).find_equivalent_units(
                equivalencies=u.spectral())
        self._spectral_axis_unit_equivalencies_titles = [
            u.Unit(unit).long_names[0].title()
            if len(u.Unit(unit).long_names) > 0 else u.Unit(unit).to_string()
            for unit in self._spectral_axis_unit_equivalencies]

        # Gets all possible conversions for flux from current spectral axis and corresponding units
        self._data_unit_equivalencies = u.Unit(
            self.hub.plot_widget.data_unit).find_equivalent_units(
                equivalencies=u.spectral_density(self.hub.data_item.spectral_axis[0]), include_prefix_units=False)
        self._data_unit_equivalencies_titles = [
            u.Unit(unit).long_names[0].title()
            if hasattr(u.Unit(unit), "long_names") and len(u.Unit(unit).long_names) > 0 else u.Unit(unit).to_string()
            for unit in self._data_unit_equivalencies]

        # Holder values for current data unit and spectral axis unit
        self.current_data_unit = self._data_unit_equivalencies_titles[0]
        self.current_spectral_axis_unit = self._spectral_axis_unit_equivalencies_titles[0]

        try:
            # Set the current data units to be the ones in plot_widget
            if hasattr(u.Unit(self.hub.plot_widget.data_unit), "long_names") and len(u.Unit(self.hub.plot_widget.data_unit).long_names) > 0:
                self.current_data_unit = u.Unit(
                    self.hub.plot_widget.data_unit).long_names[0].title()
            else:
                self.current_data_unit = u.Unit(
                    self.hub.plot_widget.data_unit).to_string()

            # Add current unit used by PlotWidget to the list of equivalencies
            # that fills the combobox
            if u.Unit(self.hub.plot_widget.data_unit) not in self._data_unit_equivalencies or \
                    self.current_data_unit not in self._data_unit_equivalencies_titles:
                self._data_unit_equivalencies.append(
                    u.Unit(self.hub.plot_widget.data_unit))
                self._data_unit_equivalencies_titles.append(
                    self.current_data_unit)

        except Exception as e:
            self.current_data_unit = self._spectral_axis_unit_equivalencies_titles[0]
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            logging.error(e)

        try:
            # Set the current spectral_axis unit to be the ones in plot_widget
            if hasattr(u.Unit(self.hub.plot_widget.data_unit), "long_names") and len(u.Unit(self.hub.plot_widget.spectral_axis_unit).long_names) > 0:
                self.current_spectral_axis_unit = u.Unit(
                    self.hub.plot_widget.spectral_axis_unit).long_names[0].title()
            else:
                self.current_spectral_axis_unit = u.Unit(
                    self.hub.plot_widget.spectral_axis_unit).to_string()

            # Add current unit used by PlotWidget to the list of equivalencies
            # that fills the combobox
            if u.Unit(self.hub.plot_widget.spectral_axis_unit) not in self._spectral_axis_unit_equivalencies or \
                    self.current_spectral_axis_unit not in self._spectral_axis_unit_equivalencies_titles:
                self._spectral_axis_unit_equivalencies.append(
                    u.Unit(self.hub.plot_widget.spectral_axis_unit))
                self._spectral_axis_unit_equivalencies_titles.append(
                    self.current_spectral_axis_unit)

            # if self.current_spectral_axis_unit not in self._spectral_axis_unit_equivalencies_titles:
            #     self._spectral_axis_unit_equivalencies_titles.append(
            #         self.current_spectral_axis_unit)
        except Exception as e:
            self.current_spectral_axis_unit = self._spectral_axis_unit_equivalencies_titles[0]
            self.ui.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            logging.error(e)

        # This gives the user the option to use their own units. These units are checked by u.Unit()
        # and PlotDataItem.is_spectral_axis_unit_compatible(spectral_axis_unit) and
        # PlotDataItem.is_data_unit_compatible(data_unit)
        self._spectral_axis_unit_equivalencies_titles.append("Custom")
        self._data_unit_equivalencies_titles.append("Custom")

        self.setup_ui()
        self.setup_connections()

        super().exec_()

    @plugin.plot_bar("Change Units", icon=QIcon(":/icons/012-file.svg"))
    def on_action_triggered(self):
        self.exec_()

    def setup_ui(self):
        """Setup the PyQt UI for this dialog."""
        # Find the current unit in the list used to fill the combobox and set it as the current text
        self.ui.comboBox_spectral.addItems(self._spectral_axis_unit_equivalencies_titles)
        index = self._spectral_axis_unit_equivalencies_titles.index(self.current_spectral_axis_unit)
        self.ui.comboBox_spectral.setCurrentIndex(index) if index > 0 else False
        self.ui.label_convert_spectral.setText(
            "Convert X axis units from {} to: ".format(self.current_spectral_axis_unit))

        # Find the current unit in the list used to fill the combobox and set it as the current text
        self.ui.comboBox_units.addItems(self._data_unit_equivalencies_titles)

        index = self._data_unit_equivalencies_titles.index(self.current_data_unit)
        self.ui.comboBox_units.setCurrentIndex(index) if index > 0 else False
        self.ui.label_convert_units.setText("Convert Y axis units from {} to: ".format(self.current_data_unit))

        # Hide custom unit options until it is chosen in the combobox
        self.ui.line_custom_spectral.hide()
        self.ui.label_valid_spectral.hide()

        self.ui.line_custom_units.hide()
        self.ui.label_valid_units.hide()

        # TODO: Implement option to preview the effect unit change will have on data
        self.ui.label_preview.hide()
        self.ui.label_preview_values.hide()

    def setup_connections(self):
        """Setup signal/slot connections for this dialog."""
        self.ui.comboBox_spectral.currentTextChanged.connect(lambda: self.on_combobox_change("X"))
        self.ui.line_custom_spectral.textChanged.connect(lambda: self.on_line_custom_units_change("X"))

        self.ui.comboBox_units.currentTextChanged.connect(lambda: self.on_combobox_change("Y"))
        self.ui.line_custom_units.textChanged.connect(lambda: self.on_line_custom_units_change("Y"))

        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.on_accepted)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.on_canceled)

    def on_combobox_change(self, axis):
        """Called when the text of the unit combo box has changed."""
        # If 'Custom', show validation label and line for entering units
        # The X axis corresponds to plot_data_item.spectral_axis_unit
        # The Y axis corresponds to plot_data_item.data_unit
        if axis == "X":
            combobox = self.ui.comboBox_spectral
            line_custom = self.ui.line_custom_spectral
            label_valid = self.ui.label_valid_spectral
        elif axis == "Y":
            combobox = self.ui.comboBox_units
            line_custom = self.ui.line_custom_units
            label_valid = self.ui.label_valid_units

        if combobox.currentText() == "Custom":
            line_custom.show()
            label_valid.show()
            label_valid.setText("Enter custom units")
            label_valid.setStyleSheet('color: green')

        else:
            line_custom.hide()
            label_valid.hide()

    def on_line_custom_units_change(self, axis):
        """Called when the text of the custom units textbox has changed."""
        # The X axis corresponds to plot_data_item.spectral_axis_unit
        # The Y axis corresponds to plot_data_item.data_unit
        if axis == "X":
            line_custom = self.ui.line_custom_spectral
            label_valid = self.ui.label_valid_spectral
        elif axis == "Y":
            line_custom = self.ui.line_custom_units
            label_valid = self.ui.label_valid_units

        # If Unit enter line is empty
        if line_custom.text() in ["", " "]:
            label_valid.setText("Enter custom units")
            label_valid.setStyleSheet('color: green')

            # Does not allow user to enter multiple spaces as valid unit
            if line_custom.text() == " ":
                line_custom.setText("")
            return

        # Try to enter the custom units
        try:
            u.Unit(line_custom.text())
            label_valid.setStyleSheet('color: green')
            label_valid.setText("{} is Valid".format(line_custom.text()))

        except Exception as e:
            # Take error message, break it up, and take the suggestions part and show it to the user
            log.debug(e)
            err = str(e)
            if "Did you mean " in err:
                similar_valid_units = err.split("Did you mean ")[1][:-1]
                label_valid.setText("Invalid, try: {}".format(similar_valid_units))
            else:
                label_valid.setText("Invalid")

            label_valid.setStyleSheet('color: red')

    def on_accepted(self):
        """Called when the user clicks the "Ok" button of the dialog."""
        if self.ui.comboBox_units.currentText() == "Custom":

            # Try to enter the custom units
            try:
                u.Unit(self.ui.line_custom_units.text())
            except Exception as e:
                log.warning("DID NOT CHANGE UNITS. {}".format(e))
                self.close()
                return False

            # If there are no units, just close the dialog and return False
            if self.ui.line_custom_units.text() in ["", " "]:
                log.warning("No custom units entered, units did not change")
                self.close()
                return False

            # Converts the data_unit to something that can be used by PlotWidget
            self.current_data_unit = self.line_custom_units.text()
            data_unit_formatted = u.Unit(self.current_data_unit).to_string()

            # Checks to make sure data_unit is compatible
            for plot_data_item in self.hub.plot_widget.listDataItems():
                if not plot_data_item.is_data_unit_compatible(data_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(data_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.hub.plot_widget.data_unit = data_unit_formatted

        else:
            # Converts the data_unit to something that can be used by PlotWidget
            self.current_data_unit = self.ui.comboBox_units.currentText()
            current_data_unit_in_u = self._data_unit_equivalencies[self._data_unit_equivalencies_titles.index(self.current_data_unit)]
            data_unit_formatted = u.Unit(current_data_unit_in_u).to_string()

            # Checks to make sure data_unit is compatible
            for plot_data_item in self.hub.plot_widget.listDataItems():
                if not plot_data_item.is_data_unit_compatible(data_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(data_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.hub.plot_widget.data_unit = data_unit_formatted

        if self.ui.comboBox_spectral.currentText() == "Custom":

            # Try to enter the custom units
            try:
                u.Unit(self.ui.line_custom_spectral.text())
            except Exception as e:
                log.warning("DID NOT CHANGE UNITS. {}".format(e))
                self.close()
                return False

            # If there are no units, just close the dialog and return False
            if self.ui.line_custom_spectral.text() in ["", " "]:
                log.warning("No custom units entered, units did not change")
                self.close()
                return False

            # Converts the spectral_axis_unit to something that can be used by PlotWidget
            self.current_spectral_axis_unit = self.line_custom_spectral.text()
            spectral_axis_unit_formatted = u.Unit(self.current_spectral_axis_unit).to_string()

            # Checks to make sure spectral_axis_unit is compatible
            for plot_data_item in self.hub.plot_widget.listDataItems():
                if not plot_data_item.is_spectral_axis_unit_compatible(spectral_axis_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(spectral_axis_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.hub.plot_widget.spectral_axis_unit = spectral_axis_unit_formatted

        else:
            # Converts the spectral_axis_unit to something that can be used by PlotWidget
            self.current_spectral_axis_unit = self.ui.comboBox_spectral.currentText()
            current_spectral_axis_unit_in_u = self._spectral_axis_unit_equivalencies[self._spectral_axis_unit_equivalencies_titles.index(self.current_spectral_axis_unit)]
            spectral_axis_unit_formatted = u.Unit(current_spectral_axis_unit_in_u).to_string()

            # Checks to make sure spectral_axis_unit is compatible
            for plot_data_item in self.hub.plot_widget.listDataItems():
                if not plot_data_item.is_spectral_axis_unit_compatible(spectral_axis_unit_formatted):
                    log.warning("DID NOT CHANGE UNITS. {} NOT COMPATIBLE".format(spectral_axis_unit_formatted))
                    self.close()
                    return False

            # Set new units
            self.hub.plot_widget.spectral_axis_unit = spectral_axis_unit_formatted

        self.close()
        return True

    def on_canceled(self):
        """Called when the user clicks the "Cancel" button of the dialog."""
        self.close()
