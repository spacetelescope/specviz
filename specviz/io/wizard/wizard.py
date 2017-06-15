import os
import sys

import numpy as np

from qtpy.QtWidgets import QApplication, QDialog, QVBoxLayout, QWidget, QPlainTextEdit
from qtpy.QtCore import Qt
from qtpy.uic import loadUi

from astropy import units as u
from astropy.io import fits

import pyqtgraph as pg

from parse_fits import parse_fits, simplify_arrays

# Units are case-sensitive so we can't simply convert all units to lowercase,
# hence why we have different capitalizations here.

DISPERSION_UNITS = [u.Angstrom, u.nm, u.um, u.mm, u.cm, u.m, u.Hz, u.kHz, u.MHz, u.GHz, u.THz]
DATA_UNITS = [u.uJy, u.mJy, u.Jy, u.erg / u.cm**2 / u.s / u.Hz, u.erg / u.cm**2 / u.s / u.um, u.erg / u.cm**2 / u.s]

# Main wizard classes

class YAMLPreviewWidget(QWidget):

    def __init__(self, parent=None):
        super(YAMLPreviewWidget, self).__init__(parent=parent)
        self.setWindowFlags(Qt.Drawer)
        self.text_editor = QPlainTextEdit()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_editor)
        self.setLayout(self.layout)


class ImportWizard(QDialog):
    pass


class HDUColumnHelper(object):

    def __init__(self, hdulist, combo_hdu, combo_column, label_status,
                 combo_units, valid_units, custom_units):

        self.hdulist = hdulist
        self.combo_hdu = combo_hdu
        self.combo_column = combo_column
        self.label_status = label_status
        self.combo_units = combo_units
        self.custom_units = custom_units
        self.valid_units = valid_units

        self.combo_hdu.clear()

        for hdu_name, hdu in self.hdulist.items():
            self.combo_hdu.addItem(hdu_name)

        self.combo_hdu.currentIndexChanged.connect(self._hdu_changed)
        self.combo_column.currentIndexChanged.connect(self._column_changed)

        self.combo_units.clear()

        for unit in valid_units:
            self.combo_units.addItem(str(unit), userData=unit)
        self.combo_units.addItem('Custom', userData='Custom')
        self.combo_units.currentIndexChanged.connect(self._unit_changed)

        self.custom_units.textChanged.connect(self._custom_unit_changed)

        self._unit_changed()

    @property
    def hdu_name(self):
        return self.combo_hdu.currentText()

    @property
    def hdu(self):
        return self.hdulist[self.hdu_name]

    @property
    def column(self):
        return self.combo_column.currentData()

    @property
    def unit(self):
        return self.combo_units.currentText() or self.custom_units.text()

    @property
    def data(self):
        if self.column is None:
            return None
        else:
            return self.hdu[self.column]['data']

    def _hdu_changed(self, event=None):
        self.combo_column.blockSignals(True)
        self.combo_column.clear()
        self.combo_column.setEnabled(True)
        model = self.combo_column.model()
        for icolumn, column_name in enumerate(self.hdu):
            column = self.hdu[column_name]
            col_shape = column['shape']
            self.combo_column.addItem(column_name + ' - shape={0}'.format(col_shape),
                                      userData=column_name)
            # Check whether column is 1-dimensional - we allow arrays that
            # are multi-dimensional but where all but one dimension is 1.
            if np.product(col_shape) != np.max(col_shape):
                item = model.item(icolumn)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        self.combo_column.blockSignals(False)
        self.combo_column.currentIndexChanged.emit(self.combo_column.currentIndex())
        self._column_changed()

    def _column_changed(self):

        unit = self.hdu[self.column]['unit']

        print("UNIT", unit)

        if unit is None:
            unit = ''
            custom_unit = True
        else:
            try:
                unit = u.Unit(unit)
            except ValueError:
                custom_unit = True
            else:
                for valid_unit in self.valid_units:
                    if unit == valid_unit:
                        unit = valid_unit
                        custom_unit = False
                        break
                else:
                    unit = str(unit)
                    custom_unit = True

        if custom_unit:
            index = self.combo_units.findText('Custom')
            self.combo_units.setCurrentIndex(index)
            self.custom_units.setText(unit)
        else:
            index = self.valid_units.index(unit)

        self.combo_units.setCurrentIndex(index)

    def _unit_changed(self):
        if self.combo_units.itemText(self.combo_units.currentIndex()) == 'Custom':
            self.custom_units.setEnabled(True)
            self.custom_units.show()
        else:
            self.custom_units.setEnabled(False)
            self.custom_units.hide()
            self.label_status.setText('')

    def _custom_unit_changed(self):
        unit = self.custom_units.text()
        if unit == '':
            self.label_status.setText('')
        else:
            u.Unit(unit)
            # try:
            #     Unit(unit)
            # except:
            #     self.label_status.setText('Invalid units')
            #     self.label_status.setStyleSheet('color: red')
            # else:
            #     self.label_status.setText('Valid units')
            #     self.label_status.setStyleSheet('color: green')


class FITSImportWizard(ImportWizard):
    """
    A wizard to help with importing spectra from files
    """

    def __init__(self, filename, parent=None):

        super(FITSImportWizard, self).__init__(parent=parent)

        self.ui = loadUi(os.path.join(os.path.dirname(__file__), 'fits_wizard.ui'), self)

        self.hdulist = simplify_arrays(parse_fits(filename))

        self.helper_disp = HDUColumnHelper(self.hdulist,
                                           self.ui.combo_dispersion_hdu,
                                           self.ui.combo_dispersion_column,
                                           self.ui.label_dispersion_status,
                                           self.ui.combo_dispersion_units,
                                           DISPERSION_UNITS,
                                           self.ui.value_dispersion_units)

        self.helper_data = HDUColumnHelper(self.hdulist,
                                           self.ui.combo_data_hdu,
                                           self.ui.combo_data_column,
                                           self.ui.label_data_status,
                                           self.ui.combo_data_units,
                                           DATA_UNITS,
                                           self.ui.value_data_units)


        self.helper_unce = HDUColumnHelper(self.hdulist,
                                           self.ui.combo_uncertainty_hdu,
                                           self.ui.combo_uncertainty_column,
                                           self.ui.label_uncertainty_status,
                                           self.ui.combo_uncertainty_units,
                                           DATA_UNITS,
                                           self.ui.value_uncertainty_units)

        self.yaml_preview = YAMLPreviewWidget(self.ui)
        self.yaml_preview.hide()
        self.ui.button_yaml.clicked.connect(self._toggle_yaml_preview)

        self.ui.combo_uncertainty_type.addItem('Standard Deviation')
        self.ui.combo_uncertainty_type.addItem('Inverse Variance')

        pg.setConfigOption('foreground', 'k')

        self.plot_widget = pg.PlotWidget(title="Spectrum preview",
                                         parent=self,
                                         background=None)
        self.layout_preview.addWidget(self.plot_widget)

        self.ui.combo_dispersion_column.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_data_column.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_column.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_type.currentIndexChanged.connect(self._update_preview)

        # NOTE: if we are worried about performance, we could have a separate
        # method to update just the axis labels, but for now this works.
        self.ui.combo_dispersion_units.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_data_units.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_units.currentIndexChanged.connect(self._update_preview)

    def _update_preview(self, event):

        x = self.helper_disp.data
        y = self.helper_data.data
        yerr = self.helper_unce.data

        if x is None or y is None:
            return

        self.plot_widget.clear()

        if x.shape != y.shape:
            # TODO: status message
            return

        if yerr is not None and self.combo_uncertainty_type.currentText() == 'Inverse Variance':
            yerr = np.sqrt(1 / yerr)

        pen = pg.mkPen('k')

        self.plot_widget.plot(x, y, pen=pen)
        self.plot_widget.autoRange()

        self.plot_widget.setLabels(left='{0} [{1}]'.format(self.helper_data.column,
                                                           self.helper_data.unit),
                                   bottom='{0} [{1}]'.format(self.helper_disp.column,
                                                             self.helper_disp.unit))

        if yerr is not None and yerr.shape == y.shape:
            err = pg.ErrorBarItem(x=x, y=y, height=yerr, pen=pen)
            self.plot_widget.addItem(err)

    def _toggle_yaml_preview(self, event):
        if self.ui.button_yaml.isChecked():
            self.yaml_preview.setWindowFlags(Qt.Drawer)
            self.yaml_preview.show()
        else:
            self.yaml_preview.setWindowFlags(Qt.Drawer)
            self.yaml_preview.hide()


if __name__ == "__main__":

    app = QApplication([])
    # dialog = FITSImportWizard('spectra/spec1d.1100.013.11002293.fits')
    dialog = FITSImportWizard(sys.argv[1])
    dialog.exec_()

# app.exec_()
