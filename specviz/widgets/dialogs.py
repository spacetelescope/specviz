"""
UI Dialog definitions
"""
from qtpy.QtWidgets import (QSizePolicy, QVBoxLayout, QHBoxLayout, QLabel,
                            QComboBox, QDialog, QGroupBox, QLineEdit,
                            QDialogButtonBox, QFormLayout)
from qtpy.QtGui import QDoubleValidator, QValidator
from qtpy.QtCore import Qt
from qtpy.uic import loadUi

from astropy.units import Unit
from astropy.units import Quantity, LogQuantity, LogUnit, spectral_density, spectral

import logging
import os

from .utils import UI_PATH
from .resources import *

from ..core.events import dispatch

class UiTopAxisDialog(QDialog):
    """
    Initialize all the TopAxisDialog Qt UI elements.
    """
    def __init__(self, *args, **kwargs):
        super(UiTopAxisDialog, self).__init__(*args, **kwargs)
        self.setObjectName("Top Axis Dialog")

        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)

        # Dialog settings
        self.setWindowTitle("Axis Settings")

        self.layout_vertical = QVBoxLayout(self)
        self.layout_horizontal = QHBoxLayout()
        self.layout_vertical.addLayout(self.layout_horizontal)

        # Define header selectors
        self.label_axis_mode = QLabel(self)
        self.combo_box_axis_mode = QComboBox(self)

        self.label_axis_mode.setText("Axis mode")

        self.layout_horizontal.addWidget(self.label_axis_mode)
        self.layout_horizontal.addWidget(self.combo_box_axis_mode)

        # Define velocity
        self.group_box_velocity = QGroupBox(self)
        self.label_reference_wavelength = QLabel(self.group_box_velocity)
        self.line_edit_reference_wavelength = QLineEdit(self.group_box_velocity)

        self.group_box_velocity.setTitle("Velocity parameters")
        self.label_reference_wavelength.setText("Reference wavelength")

        self.layout_horizontal_2 = QHBoxLayout(self.group_box_velocity)
        self.layout_horizontal_2.addWidget(self.label_reference_wavelength)
        self.layout_horizontal_2.addWidget(self.line_edit_reference_wavelength)

        self.layout_vertical.addWidget(self.group_box_velocity)

        # Define redshift
        self.group_box_redshift = QGroupBox(self)
        self.label_redshift = QLabel(self.group_box_redshift)
        self.line_edit_redshift = QLineEdit(
            self.group_box_redshift)

        self.group_box_redshift.setTitle("Redshift parameters")
        self.label_redshift.setText("Amount")

        self.layout_horizontal_3 = QHBoxLayout(self.group_box_redshift)
        self.layout_horizontal_3.addWidget(self.label_redshift)
        self.layout_horizontal_3.addWidget(self.line_edit_redshift)

        self.layout_vertical.addWidget(self.group_box_redshift)

        # Add a spacer
        self.layout_vertical.addStretch(1)

        # Buttons
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel
                                           | QDialogButtonBox.Ok)
        self.button_box.setObjectName("buttonBox")
        self.layout_vertical.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


class TopAxisDialog(UiTopAxisDialog):
    def __init__(self, parent=None):
        super(TopAxisDialog, self).__init__(parent)
        self.ref_wave = 0.0
        self.redshift = 0.0

        # Set validators
        self.line_edit_reference_wavelength.setValidator(
            QDoubleValidator())
        self.line_edit_redshift.setValidator(
            QDoubleValidator())

        # Populate options
        self.combo_box_axis_mode.addItems(
            ['Velocity', 'Redshift', 'Pixel'])

        # Setup connections
        self._setup_connections()
        self._on_select(0)

    def _setup_connections(self):
        # Show/hide corresponding container when mode is selected
        self.combo_box_axis_mode.currentIndexChanged.connect(self._on_select)

    def set_current_unit(self, unit):
        self.wgt_ref_wave_unit.setText(unit)

    def _on_select(self, index):
        if index == 0:
            self.group_box_velocity.show()
            self.group_box_redshift.hide()
        elif index == 1:
            self.group_box_velocity.hide()
            self.group_box_redshift.show()
        else:
            self.group_box_velocity.hide()
            self.group_box_redshift.hide()

    def accept(self):
        self.mode = self.combo_box_axis_mode.currentIndex()

        rw_val = str(self.line_edit_reference_wavelength.text())
        self.ref_wave = float(rw_val) if rw_val != '' else self.ref_wave
        rs = str(self.line_edit_redshift.text())
        self.redshift = float(rs) if rs != '' else self.redshift

        # Notify of redshift change
        dispatch.change_redshift.emit(self.redshift)

        super(TopAxisDialog, self).accept()

    def reject(self):
        super(TopAxisDialog, self).reject()


class UiLayerArithmeticDialog(QDialog):
    def __init__(self, parent=None):
        super(UiLayerArithmeticDialog, self).__init__(parent)

        # Dialog settings
        self.setWindowTitle("Layer Arithmetic")
        self.resize(354, 134)

        self.layout_vertical = QVBoxLayout(self)

        # Arithmetic group box
        self.group_box_arithmetic = QGroupBox(self)
        self.group_box_arithmetic.setTitle("Formula")

        self.line_edit_formula = QLineEdit(self.group_box_arithmetic)

        self.layout_horizontal = QHBoxLayout(self.group_box_arithmetic)
        self.layout_horizontal.addWidget(self.line_edit_formula)
        self.layout_vertical.addWidget(self.group_box_arithmetic)

        # Buttons
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.layout_vertical.addWidget(self.button_box)


class LayerArithmeticDialog(UiLayerArithmeticDialog):
    def __init__(self, parent=None):
        super(LayerArithmeticDialog, self).__init__(parent)


class UiUnitChangeDialog(QDialog):
    def __init__(self, parent=None):
        super(UiUnitChangeDialog, self).__init__(parent)

        # Dialog settings
        self.setWindowTitle("Change Plot Units")

        self.layout_vertical = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        self.layout_vertical.addLayout(self.form_layout)

        # Flux unit
        self.label_flux_unit = QLabel(self)
        self.line_edit_flux_unit = QLineEdit(self)

        self.label_flux_unit.setText("Flux Unit")

        self.form_layout.addRow(self.label_flux_unit, self.line_edit_flux_unit)

        # Dispersion unit
        self.label_disp_unit = QLabel(self)
        self.line_edit_disp_unit = QLineEdit(self)

        self.label_disp_unit.setText("Dispersion Unit")

        self.form_layout.addRow(self.label_disp_unit, self.line_edit_disp_unit)

        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.layout_vertical.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


class UnitChangeDialog(UiUnitChangeDialog):
    def __init__(self, parent=None):
        super(UnitChangeDialog, self).__init__(parent)
        self._layer = None
        self._flux_unit = None
        self._disp_unit = None

        self.line_edit_disp_unit.textChanged.connect(self.check_state)
        self.line_edit_disp_unit.textChanged.emit(self.line_edit_disp_unit.text())

        self.line_edit_flux_unit.textChanged.connect(self.check_state)
        self.line_edit_flux_unit.textChanged.emit(self.line_edit_flux_unit.text())

    def set_layer(self, layer):
        self._layer = layer

        self.line_edit_flux_unit.setValidator(DataUnitValidator(self._layer))
        self.line_edit_disp_unit.setValidator(DispersionUnitValidator(self._layer))

        self.line_edit_disp_unit.setText("{}".format(self._layer.dispersion_unit))
        self.line_edit_flux_unit.setText("{}".format(self._layer.unit))

    @property
    def disp_unit(self):
        return self.line_edit_disp_unit.text()

    @property
    def flux_unit(self):
        return self.line_edit_flux_unit.text()

    def accept(self):
        super(UnitChangeDialog, self).accept()

    def reject(self):
        super(UnitChangeDialog, self).reject()

    def check_state(self, *args, **kwargs):
        sender = self.sender()

        validator = sender.validator()

        if validator is None:
            return

        state = validator.validate(sender.text(), 0)[0]
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        if state == QValidator.Acceptable:
            color = '#c4df9b' # green
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        elif state == QValidator.Intermediate:
            color = '#fff79a' # yellow
        else:
            color = '#f6989d' # red

        sender.setStyleSheet(
            "QLineEdit {{ background-color: {} }}".format(color))


class DataUnitValidator(QValidator):
    def __init__(self, layer, *args, **kwargs):
        super(DataUnitValidator, self).__init__(*args, **kwargs)

        self._layer = layer

    def validate(self, p_str, p_int):
        try:
            unit = Unit(p_str)

            if self._layer.unit.is_unity() or unit.is_equivalent(self._layer.unit,
                                  equivalencies=spectral_density(
                                      self._layer.masked_dispersion.data)):
                return (QValidator.Acceptable, p_str, p_int)
            else:
                return (QValidator.Intermediate, p_str, p_int)
        except ValueError as e:
            return (QValidator.Intermediate, p_str, p_int)

        return (QValidator.Invalid, p_str, p_int)

    def fixup(self, p_str):
        p_str.replace(p_str, "{}".format(self._layer.unit))


class DispersionUnitValidator(QValidator):
    def __init__(self, layer, *args, **kwargs):
        super(DispersionUnitValidator, self).__init__(*args, **kwargs)

        self._layer = layer

    def validate(self, p_str, p_int):
        try:
            unit = Unit(p_str)

            if self._layer.dispersion_unit.is_unity() or unit.is_equivalent(
                self._layer.dispersion_unit, equivalencies=spectral()):
                return (QValidator.Acceptable, p_str, p_int)
            else:
                return (QValidator.Intermediate, p_str, p_int)
        except ValueError as e:
            return (QValidator.Intermediate, p_str, p_int)

        return (QValidator.Invalid, p_str, p_int)

    def fixup(self, p_str):
        p_str.replace(p_str, "{}".format(self._layer.dispersion_unit))


class UiSmoothingDialog(QDialog):
    """
    Initialize all the TopAxisDialog Qt UI elements.
    """
    def __init__(self, *args, **kwargs):
        super(UiSmoothingDialog, self).__init__(*args, **kwargs)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        self.setSizePolicy(size_policy)

        # Dialog settings
        self.setWindowTitle("Smoothing Dialog")

        self.layout_vertical = QVBoxLayout(self)
        self.layout_horizontal = QHBoxLayout()
        self.layout_vertical.addLayout(self.layout_horizontal)

        # Define header selectors
        self.label_axis_mode = QLabel(self)
        self.combo_box_kernel = QComboBox(self)

        self.label_axis_mode.setText("Kernel")

        self.layout_horizontal.addWidget(self.label_axis_mode)
        self.layout_horizontal.addWidget(self.combo_box_kernel)
        self.layout_horizontal.setStretch(1, 1)

        # Define velocity
        self.group_box = QGroupBox(self)
        self.label_stddev = QLabel(self.group_box)
        self.line_edit_stddev = QLineEdit(self.group_box)

        self.group_box.setTitle("Parameters")
        self.label_stddev.setText("Standard Deviation (pixels)")

        self.layout_horizontal_2 = QHBoxLayout(self.group_box)
        self.layout_horizontal_2.addWidget(self.label_stddev)
        self.layout_horizontal_2.addWidget(self.line_edit_stddev)

        self.layout_vertical.addWidget(self.group_box)

        # Add a spacer
        self.layout_vertical.addStretch(1)

        # Buttons
        self.button_box = QDialogButtonBox(self)
        self.button_box.setOrientation(Qt.Horizontal)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel
                                           | QDialogButtonBox.Ok)
        self.button_box.setObjectName("buttonBox")
        self.layout_vertical.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)


class SmoothingDialog(UiSmoothingDialog):
    def __init__(self, *args, **kwargs):
        super(SmoothingDialog, self).__init__(*args, **kwargs)

        self.combo_box_kernel.addItem("Gaussian")

        self._selected_ind = None
        self._kernel = None
        self._args = None

        self.setup_connections()

        self._on_select(0)

    def setup_connections(self):
        self.combo_box_kernel.currentIndexChanged.connect(self._on_select)

    def _on_select(self, index):
        pass

    def accept(self):
        self._kernel = 'Gaussian1DKernel'

        try:
            self._args = [float(self.line_edit_stddev.text())]

            super(SmoothingDialog, self).accept()
        except ValueError as e:
            logging.error(e)

    def reject(self):
        super(SmoothingDialog, self).reject()

    @property
    def kernel(self):
        return self._kernel

    @property
    def args(self):
        return self._args


class ResampleDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(ResampleDialog, self).__init__(*args, **kwargs)
        # Load the interpolation warning dialog
        loadUi(os.path.join(UI_PATH, "dialog_resample_warning.ui"), self)

        self._methods = {
            "Linear": 'linear',
            "Nearest": 'nearest',
            "Zeroth-order Spline": 'zero',
            "First-order Spline": 'slinear',
            "Second-order Spline": 'quadratic',
            "Third-order Spline": 'cubic'
        }

        # Update the available options
        self.method_combo_box.clear()
        self.method_combo_box.addItems(list(self._methods.keys()))

        # Set default
        self._current_method = 'linear'

    def accept(self):
        self._current_method = self._methods[self.method_combo_box.currentText()]

        super(ResampleDialog, self).accept()

    @property
    def method(self):
        return self._current_method
