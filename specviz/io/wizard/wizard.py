# The import wizard is implemented in a way that is not specific to any given
# file format, but instead has the concept that a file can include one or more
# datasets, and a dataset can include one or more components. In the case of
# a FITS file, the datasets are HDUs, and components can be columns, standalone
# components (in the case of a Primary or ImageHDU), or spectral WCS for
# example.

import os
import sys
from collections import OrderedDict

import yaml
import numpy as np

from qtpy.QtWidgets import QApplication, QDialog, QVBoxLayout, QWidget, QPlainTextEdit
from qtpy.QtCore import Qt
from qtpy.uic import loadUi

from astropy import units as u

import pyqtgraph as pg


def represent_dict_order(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(OrderedDict, represent_dict_order)

# We list here the units that appear in the pre-defined list of units for each
# component. If a unit is not found, 'Custom' will be selected and a field will
# allow the user to edit the units. Here we should add any common units to make
# it easier for users.
DISPERSION_UNITS = [u.Angstrom, u.nm, u.um, u.mm, u.cm, u.m,
                    u.Hz, u.kHz, u.MHz, u.GHz, u.THz]
DATA_UNITS = [u.uJy, u.mJy, u.Jy, u.erg / u.cm**2 / u.s / u.Hz,
              u.erg / u.cm**2 / u.s / u.um, u.erg / u.cm**2 / u.s]


class YAMLPreviewWidget(QWidget):
    """
    A YAML preview widget that appears as a drawer on the side of the main
    import widget.
    """

    def __init__(self, parent=None):
        super(YAMLPreviewWidget, self).__init__(parent=parent)
        self.setWindowFlags(Qt.Drawer)
        self.text_editor = QPlainTextEdit()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_editor)
        self.setLayout(self.layout)

    def set_text(self, text):
        self.text_editor.setPlainText(text)


class ComponentHelper(object):
    """
    Since for each component we need to define the logic between the dataset,
    component, and unit selection, we use this helper class to manage this and
    then use it three times.
    """

    def __init__(self, datasets, combo_dataset, combo_component, combo_units,
                 valid_units, custom_units, label_status):

        self.datasets = datasets

        self.combo_dataset = combo_dataset
        self.combo_component = combo_component
        self.combo_units = combo_units
        self.valid_units = valid_units
        self.custom_units = custom_units
        self.label_status = label_status

        # Initialize combo box of datasets. We don't expect this to change
        # so we can just do it here.

        self.combo_dataset.clear()

        for dataset_name, dataset in self.datasets.items():
            self.combo_dataset.addItem(dataset_name)

        # Similarly, we set up the combo of pre-defined units

        self.combo_units.clear()

        for unit in valid_units:
            self.combo_units.addItem(str(unit), userData=unit)
        self.combo_units.addItem('Custom', userData='Custom')

        # Set up callbacks for various events
        self.combo_dataset.currentIndexChanged.connect(self._dataset_changed)
        self.combo_component.currentIndexChanged.connect(self._component_changed)
        self.combo_units.currentIndexChanged.connect(self._unit_changed)
        self.custom_units.textChanged.connect(self._custom_unit_changed)

        # We now force combos to update
        self._dataset_changed()
        self._unit_changed()
        self._custom_unit_changed()

    @property
    def dataset_name(self):
        return self.combo_dataset.currentIndex()

    @property
    def dataset_name(self):
        return self.combo_dataset.currentText()

    @property
    def dataset(self):
        return self.datasets[self.dataset_name]

    @property
    def component_index(self):
        return self.combo_component.currentIndex()

    @property
    def component_name(self):
        return self.combo_component.currentData()

    @property
    def component(self):
        return self.combo_component.currentData()

    @property
    def unit(self):
        combo_text = self.combo_units.currentText()
        if combo_text == 'Custom':
            return self.custom_units.text()
        else:
            return combo_text

    @property
    def data(self):
        if self.component is None:
            return None
        else:
            return self.dataset[self.component]['data']

    def _dataset_changed(self, event=None):
        self.combo_component.blockSignals(True)
        self.combo_component.clear()
        self.combo_component.setEnabled(True)
        model = self.combo_component.model()
        for icomponent, component_name in enumerate(self.dataset):
            component = self.dataset[component_name]
            col_shape = component['shape']
            self.combo_component.addItem(component_name + ' - shape={0}'.format(col_shape),
                                         userData=component_name)
            # Check whether component is 1-dimensional - we allow arrays that
            # are multi-dimensional but where all but one dimension is 1.
            if np.product(col_shape) != np.max(col_shape):
                item = model.item(icomponent)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
        self.combo_component.blockSignals(False)
        self.combo_component.currentIndexChanged.emit(self.combo_component.currentIndex())
        self._component_changed()

    def _component_changed(self):

        unit = self.dataset[self.component]['unit']

        if unit is None:
            unit = ''
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
            try:
                u.Unit(unit)
            except:
                self.label_status.setText('Invalid units')
                self.label_status.setStyleSheet('color: red')
            else:
                self.label_status.setText('Valid units')
                self.label_status.setStyleSheet('color: green')


class BaseImportWizard(QDialog):
    """
    A wizard to help with importing spectra from files.
    """

    dataset_label = 'Dataset'

    def __init__(self, datasets, parent=None):

        super(BaseImportWizard, self).__init__(parent=parent)

        self.datasets = datasets

        self.ui = loadUi(os.path.join(os.path.dirname(__file__), 'wizard.ui'), self)

        for label in [self.ui.label_dispersion_dataset,
                      self.ui.label_data_dataset,
                      self.ui.label_uncertainty_dataset]:
            label.setText(label.text().replace('{{dataset}}', self.dataset_label))

        self.helper_disp = ComponentHelper(self.datasets,
                                           self.ui.combo_dispersion_dataset,
                                           self.ui.combo_dispersion_component,
                                           self.ui.combo_dispersion_units,
                                           DISPERSION_UNITS,
                                           self.ui.value_dispersion_units,
                                           self.ui.label_dispersion_status)

        self.helper_data = ComponentHelper(self.datasets,
                                           self.ui.combo_data_dataset,
                                           self.ui.combo_data_component,
                                           self.ui.combo_data_units,
                                           DATA_UNITS,
                                           self.ui.value_data_units,
                                           self.ui.label_data_status)

        self.helper_unce = ComponentHelper(self.datasets,
                                           self.ui.combo_uncertainty_dataset,
                                           self.ui.combo_uncertainty_component,
                                           self.ui.combo_uncertainty_units,
                                           DATA_UNITS,
                                           self.ui.value_uncertainty_units,
                                           self.ui.label_uncertainty_status)

        self.yaml_preview = YAMLPreviewWidget(self.ui)
        self.yaml_preview.hide()
        self.ui.button_yaml.clicked.connect(self._toggle_yaml_preview)

        self.ui.button_ok.clicked.connect(self.accept)
        self.ui.button_cancel.clicked.connect(self.reject)

        self.ui.combo_uncertainty_type.addItem('Standard Deviation', userData='std')
        self.ui.combo_uncertainty_type.addItem('Inverse Variance', userData='ivar')

        pg.setConfigOption('foreground', 'k')

        self.plot_widget = pg.PlotWidget(title="Spectrum preview",
                                         parent=self,
                                         background=None)
        self.layout_preview.addWidget(self.plot_widget)

        self.ui.combo_dispersion_component.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_data_component.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_component.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_type.currentIndexChanged.connect(self._update_preview)

        # NOTE: if we are worried about performance, we could have a separate
        # method to update just the axis labels, but for now this works.
        self.ui.combo_dispersion_units.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_data_units.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_units.currentIndexChanged.connect(self._update_preview)

        # Force a preview update in case initial guess is good
        self._update_preview()

    def accept(self, event=None):
        print(self.as_yaml())
        super(BaseImportWizard, self).accept()

    def _update_preview(self, event=None):

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

        self.plot_widget.setLabels(left='{0} [{1}]'.format(self.helper_data.component,
                                                           self.helper_data.unit),
                                   bottom='{0} [{1}]'.format(self.helper_disp.component,
                                                             self.helper_disp.unit))

        if yerr is not None and yerr.shape == y.shape:
            err = pg.ErrorBarItem(x=x, y=y, height=yerr, pen=pen)
            self.plot_widget.addItem(err)

    def _toggle_yaml_preview(self, event):
        if self.ui.button_yaml.isChecked():
            self.yaml_preview.setWindowFlags(Qt.Drawer)
            self.yaml_preview.set_text(self.as_yaml())
            self.yaml_preview.show()
        else:
            self.yaml_preview.setWindowFlags(Qt.Drawer)
            self.yaml_preview.set_text('')
            self.yaml_preview.hide()

    def as_yaml_dict(self):
        raise NotImplementedError()

    def as_yaml(self):
        yaml_dict = self.as_yaml_dict()
        string = yaml.dump(yaml_dict, default_flow_style=False)
        string = '--- !CustomLoader\n' + string
        return string


class FITSImportWizard(BaseImportWizard):
    dataset_label = 'HDU'

    def as_yaml_dict(self):
        """
        Convert the current configuration to a dictionary that can then be
        serialized to YAML
        """

        yaml_dict = OrderedDict()
        yaml_dict['name'] = 'Wizard'
        yaml_dict['extension'] = ['fits']
        if self.helper_disp.component_name.startswith('WCS::'):
            yaml_dict['wcs'] = {
            'hdu': self.helper_disp.dataset_name,
            }
        else:
            yaml_dict['dispersion'] = {
                            'hdu': self.helper_disp.dataset_name,
                            'col': self.helper_disp.component_name,
                            'unit': self.helper_disp.unit
                    }
        yaml_dict['data'] = {
                        'hdu': self.helper_data.dataset_name,
                        'col': self.helper_data.component_name,
                        'unit': self.helper_data.unit
                    }
        yaml_dict['uncertainty'] = {
                        'hdu': self.helper_unce.dataset_name,
                        'col': self.helper_unce.component_name,
                        'type': self.ui.combo_uncertainty_type.currentData()
                    }
        yaml_dict['meta'] = {'author': 'Wizard'}

        return yaml_dict


if __name__ == "__main__":

    from parse_fits import simplify_arrays, parse_fits

    app = QApplication([])
    dialog = FITSImportWizard(simplify_arrays(parse_fits(sys.argv[1])))
    dialog.exec_()
