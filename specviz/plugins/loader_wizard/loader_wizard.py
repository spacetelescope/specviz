# The import wizard is implemented in a way that is not specific to any given
# file format, but instead has the concept that a file can include one or more
# datasets, and a dataset can include one or more components. In the case of
# a FITS file, the datasets are HDUs, and components can be columns, standalone
# components (in the case of a Primary or ImageHDU), or spectral WCS for
# example.

import os
import sys
import tempfile
import uuid
from collections import OrderedDict


import specutils
import numpy as np
import pyqtgraph as pg
import yaml
from astropy import units as u
from astropy.wcs import WCS
from qtpy import compat
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont, QIcon
from qtpy.QtWidgets import QApplication, QDialog, QVBoxLayout, QWidget, QPlainTextEdit, QPushButton
from qtpy.uic import loadUi
from ...core.plugin import plugin

from .parse_fits import simplify_arrays, parse_fits
from .parse_ecsv import parse_ecsv, parse_ascii


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


class OutputPreviewWidget(QWidget):
    """
    A YAML preview widget that appears as a drawer on the side of the main
    import widget.
    """

    def __init__(self, parent=None):
        super(OutputPreviewWidget, self).__init__(parent=parent)
        self.setWindowFlags(Qt.Sheet)
        self.text_editor = QPlainTextEdit()
        self.close_button = QPushButton('Close')
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_editor)
        self.layout.addWidget(self.close_button)
        self.setLayout(self.layout)
        self.close_button.clicked.connect(self.hide)
        self.resize(400, 500)
        font = QFont('Courier')
        self.text_editor.setFont(font)
        self.text_editor.setReadOnly(True)

    def set_text(self, text):
        self.text_editor.setPlainText(text)


class ComponentHelper(object):
    """
    Since for each component we need to define the logic between the dataset,
    component, and unit selection, we use this helper class to manage this and
    then use it three times.
    """

    def __init__(self, datasets, combo_dataset, combo_component, combo_units=None,
                 valid_units=None, custom_units=None, label_status=None, allow_wcs=True):

        self.datasets = datasets

        self.combo_dataset = combo_dataset
        self.combo_component = combo_component
        self.combo_units = combo_units
        self.valid_units = valid_units
        self.custom_units = custom_units
        self.label_status = label_status
        self.allow_wcs = allow_wcs

        # Initialize combo box of datasets. We don't expect this to change
        # so we can just do it here.

        self.combo_dataset.clear()

        for dataset_name, dataset in self.datasets.items():
            self.combo_dataset.addItem(dataset_name)

        # Similarly, we set up the combo of pre-defined units

        if self.combo_units is not None:
            self.combo_units.clear()
            for unit in valid_units:
                self.combo_units.addItem(str(unit), userData=unit)
            self.combo_units.addItem('Custom', userData='Custom')

        # Set up callbacks for various events

        self.combo_dataset.currentIndexChanged.connect(self._dataset_changed)
        self.combo_component.currentIndexChanged.connect(self._component_changed)

        if self.combo_units is not None:
            self.combo_units.currentIndexChanged.connect(self._unit_changed)
        if self.custom_units is not None:
            self.custom_units.textChanged.connect(self._custom_unit_changed)

        # We now force combos to update
        self._dataset_changed()
        self._unit_changed()
        self._custom_unit_changed()

    @property
    def dataset_name(self):
        return self.combo_dataset.currentText()

    @property
    def dataset(self):
        if self.dataset_name:
            return self.datasets[self.dataset_name]
        else:
            return None

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
        if self.dataset is None or self.component is None:
            return None
        else:
            return self.dataset[self.component]['data']

    @property
    def hdu_index(self):
        if self.dataset is None or self.component is None:
            return None
        else:
            return self.dataset[self.component]['index']

    def _dataset_changed(self, event=None):

        if self.dataset is None:
            self.combo_component.setCurrentIndex(-1)
            return

        self.combo_component.blockSignals(True)
        self.combo_component.clear()
        self.combo_component.setEnabled(True)
        model = self.combo_component.model()
        icomponent = 0
        for component_name, component in self.dataset.items():
            if isinstance(component['data'], WCS):
                if not self.allow_wcs:
                    continue
                label = component_name
            else:
                col_shape = component['shape']
                label = component_name + ' - shape={0}'.format(col_shape)
            self.combo_component.addItem(label, userData=component_name)
            # Check whether component is 1-dimensional - we allow arrays that
            # are multi-dimensional but where all but one dimension is 1.
            if component['ndim'] != 1:
                item = model.item(icomponent)
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            icomponent += 1
        self.combo_component.blockSignals(False)
        self.combo_component.currentIndexChanged.emit(self.combo_component.currentIndex())
        self._component_changed()

    def _component_changed(self):

        if self.combo_units is None:
            return

        if self.dataset is None:
            self.combo_units.setCurrentIndex(-1)
            return

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

        if self.combo_units is None:
            return

        if self.combo_units.itemText(self.combo_units.currentIndex()) == 'Custom':
            self.custom_units.setEnabled(True)
            self.custom_units.show()
        else:
            self.custom_units.setEnabled(False)
            self.custom_units.hide()
            self.label_status.setText('')

    def _custom_unit_changed(self):

        if self.custom_units is None:
            return

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
        self.new_loader_dict = OrderedDict()

        self.ui = loadUi(os.path.abspath(
               os.path.join(os.path.dirname(__file__), "loader_wizard.ui")), self)

        for label in [self.ui.label_dispersion_dataset,
                      self.ui.label_data_dataset,
                      self.ui.label_uncertainty_dataset,
                      self.ui.label_mask_dataset]:
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
                                           self.ui.label_data_status,
                                           allow_wcs=False)

        self.helper_unce = ComponentHelper(self.datasets,
                                           self.ui.combo_uncertainty_dataset,
                                           self.ui.combo_uncertainty_component,
                                           allow_wcs=False)

        self.helper_mask = ComponentHelper(self.datasets,
                                           self.ui.combo_mask_dataset,
                                           self.ui.combo_mask_component,
                                           allow_wcs=False)

        self.output_preview = OutputPreviewWidget(self)
        self.output_preview.hide()
        self.ui.button_yaml.clicked.connect(self._toggle_output_preview)

        self.ui.button_ok.clicked.connect(self.accept)
        self.ui.button_cancel.clicked.connect(self.reject)

        self.ui.combo_uncertainty_type.addItem('Standard Deviation', userData='std')
        self.ui.combo_uncertainty_type.addItem('Inverse Variance', userData='ivar')

        pg.setConfigOption('foreground', 'k')

        self.plot_widget = pg.PlotWidget(title="Spectrum preview",
                                         parent=self,
                                         background=None)
        self.layout_preview.addWidget(self.plot_widget)

        self.ui.bool_uncertainties.setChecked(False)
        self.set_uncertainties_enabled(False)
        self.ui.bool_uncertainties.toggled.connect(self.set_uncertainties_enabled)

        self.ui.bool_mask.setChecked(False)
        self.set_mask_enabled(False)
        self.ui.bool_mask.toggled.connect(self.set_mask_enabled)

        self.ui.combo_bit_mask_definition.addItem('Custom', userData='custom')
        self.ui.combo_bit_mask_definition.addItem('SDSS', userData='sdss')
        self.ui.combo_bit_mask_definition.addItem('JWST', userData='jwst')

        self.ui.loader_name.textChanged.connect(self._clear_loader_name_status)

        self.ui.combo_dispersion_component.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_data_component.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_component.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_uncertainty_type.currentIndexChanged.connect(self._update_preview)

        # NOTE: if we are worried about performance, we could have a separate
        # method to update just the axis labels, but for now this works.
        self.ui.combo_dispersion_units.currentIndexChanged.connect(self._update_preview)
        self.ui.combo_data_units.currentIndexChanged.connect(self._update_preview)

        self.ui.button_save_yaml.clicked.connect(self.save_loader_script)

        # Force a preview update in case initial guess is good
        self._update_preview()
        self._clear_loader_name_status()

    def set_uncertainties_enabled(self, enabled):

        self.combo_uncertainty_dataset.blockSignals(not enabled)
        self.combo_uncertainty_component.blockSignals(not enabled)
        self.combo_uncertainty_type.blockSignals(not enabled)

        self.combo_uncertainty_dataset.setEnabled(enabled)
        self.combo_uncertainty_component.setEnabled(enabled)
        self.combo_uncertainty_type.setEnabled(enabled)

        if enabled:
            self.combo_uncertainty_dataset.setCurrentIndex(0)
            self.combo_uncertainty_type.setCurrentIndex(0)
        else:
            self.combo_uncertainty_dataset.setCurrentIndex(-1)
            self.combo_uncertainty_component.setCurrentIndex(-1)
            self.combo_uncertainty_type.setCurrentIndex(-1)

        self._update_preview()

    def set_mask_enabled(self, enabled):

        self.combo_mask_dataset.blockSignals(not enabled)
        self.combo_mask_component.blockSignals(not enabled)
        self.combo_bit_mask_definition.blockSignals(not enabled)

        self.combo_mask_dataset.setEnabled(enabled)
        self.combo_mask_component.setEnabled(enabled)
        self.combo_bit_mask_definition.setEnabled(enabled)

        if enabled:
            self.combo_mask_dataset.setCurrentIndex(0)
            self.combo_bit_mask_definition.setCurrentIndex(0)
        else:
            self.combo_mask_dataset.setCurrentIndex(-1)
            self.combo_mask_component.setCurrentIndex(-1)
            self.combo_bit_mask_definition.setCurrentIndex(-1)

    @property
    def uncertainties_enabled(self):
        return self.bool_uncertainties.isChecked()

    def accept(self, event=None):
        super(BaseImportWizard, self).accept()

    def _update_preview(self, event=None):

        self.plot_widget.clear()

        x = self.helper_disp.data
        y = self.helper_data.data
        yerr = self.helper_unce.data

        if x is None or y is None:
            return

        if isinstance(x, WCS):
            x = x.all_pix2world(np.arange(len(y)), 0)[0]

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

    def _toggle_output_preview(self, event):
        self.output_preview.set_text(self.as_new_loader())
        self.output_preview.show()

    def as_new_loader_dict(self):
        raise NotImplementedError()

    def get_template(self):
        raise NotImplementedError()

    def as_new_loader(self, name=None):

        self.as_new_loader_dict(name=name)

        print(self.new_loader_dict)

        template_path = self.get_template()

        with open(template_path, 'r') as f:
            filled_template = f.read().format(**self.new_loader_dict)

        return filled_template

    def _clear_loader_name_status(self):
        self.ui.label_loader_name_status.setText('')
        self.ui.label_loader_name_status.setStyleSheet('')

    def save_loader_script(self, event=None):
        if self.ui.loader_name.text() == "":
            self.ui.label_loader_name_status.setText('Enter a name for the loader')
            self.ui.label_loader_name_status.setStyleSheet('color: red')
            return

        specutils_dir = os.path.join(os.path.expanduser('~'), '.specutils')
        if not os.path.exists(specutils_dir):
            os.mkdir(specutils_dir)

        filename = compat.getsavefilename(parent=self,
                                          caption='Export loader to .py file',
                                          basedir=specutils_dir)[0]

        if filename == '':
            return

        filename = "{}.py".format(filename) if not filename.endswith(".py") else filename

        string = self.as_new_loader()
        with open(filename, 'w') as f:
            f.write(string)

        # Refresh loaders so new loader shows up
        # specutils.io.registers._load_user_io()

# --------- Helper methods for subclasses ------------

    def new_loader_dispersion(self):
        self.new_loader_dict['dispersion_hdu'] = self.helper_disp.hdu_index
        self.new_loader_dict['dispersion_col'] = self.helper_disp.component_name
        self.new_loader_dict['dispersion_unit'] = self.helper_disp.unit

    def new_loader_data(self):
        self.new_loader_dict['data_hdu'] = self.helper_data.hdu_index
        self.new_loader_dict['data_col'] = self.helper_data.component_name
        self.new_loader_dict['data_unit'] = self.helper_data.unit

    def new_loader_uncertainty(self):
        if self.ui.bool_uncertainties.isChecked():
            self.new_loader_dict['uncertainty_hdu'] = self.helper_unce.hdu_index
            self.new_loader_dict['uncertainty_col'] = self.helper_unce.component_name
            self.new_loader_dict['uncertainty_type'] = self.ui.combo_uncertainty_type.currentData()


class FITSImportWizard(BaseImportWizard):
    dataset_label = 'HDU'

    def as_new_loader_dict(self, name=None):
        """
        Convert the current configuration to a dictionary that can then be
        serialized to a python loader template
        """

        self.new_loader_dict['name'] = name or self.ui.loader_name.text()
        self.new_loader_dict['extension'] = ['fits']

        if self.helper_disp.component_name.startswith('WCS::'):
            self.new_loader_dict['wcs_hdu'] = self.helper_disp.hdu_index

        else:
            self.new_loader_dispersion()
            self.new_loader_dict['wcs_hdu'] = self.helper_disp.hdu_index

        self.new_loader_data()

        self.new_loader_uncertainty()

        if self.ui.bool_mask.isChecked():
            # if going to use this, might need to change this to single
            # dict items
            self.new_loader_dict['mask'] = OrderedDict()
            self.new_loader_dict['mask']['hdu'] = self.helper_mask.hdu_index
            self.new_loader_dict['mask']['col'] = self.helper_mask.component_name
            definition = self.ui.combo_bit_mask_definition.currentData()
            if definition != 'custom':
                self.new_loader_dict['mask']['definition'] = definition

        self.new_loader_dict['meta_author'] = 'Wizard'


    def get_template(self):
        if "uncertainty_hdu" in self.new_loader_dict.keys():
            template_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), ".",
                             "new_loader_fits_uncer_py.tmpl"))

        else:
            template_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), ".",
                             "new_loader_fits_py.tmpl"))

        return template_path


class ASCIIImportWizard(BaseImportWizard):
    dataset_label = 'Table'

    def as_new_loader_dict(self, name=None):
        """
        Convert the current configuration to a dictionary
        that can then be serialized to YAML
        """
        self.new_loader_dict['name'] = name or self.ui.loader_name.text()

        self.new_loader_dispersion()

        self.new_loader_data()

        self.new_loader_uncertainty()

        self.new_loader_dict['meta_author'] = 'Wizard'

        self.add_extension()


    def add_extension(self):
        self.new_loader_dict['extension'] = ['dat']


class ECSVImportWizard(ASCIIImportWizard):

    def add_extension(self):
        self.new_loader_dict['extension'] = ['ecsv']


@plugin("Loader Wizard")
class LoaderWizard(QDialog):
    @plugin.tool_bar("Loader Wizard", icon=QIcon(":/icons/012-file.svg"), location=0)
    def open_wizard(self):

        filters = ["FITS, ECSV, text (*.fits *.ecsv *.dat *.txt)"]
        filename, file_filter = compat.getopenfilename(filters=";;".join(filters))

        if filename == '':
            return

        if filename.lower().endswith('fits'):
            dialog = FITSImportWizard(simplify_arrays(parse_fits(filename)))

        elif filename.lower().endswith('ecsv'):
            dialog = ECSVImportWizard(simplify_arrays(parse_ecsv(filename)))

        elif filename.lower().endswith('dat') or filename.lower().endswith('txt'):
            dialog = ASCIIImportWizard(simplify_arrays(parse_ascii(filename)))

        else:
            raise NotImplementedError(file_filter)

        val = dialog.exec_()

        if val == 0:
            return

        # Make temporary YAML file
        yaml_file = tempfile.mktemp()
        with open(yaml_file, 'w') as f:
            f.write(dialog.as_new_loader(name=str(uuid.uuid4())))

        # Temporarily load YAML file
        # yaml_filter = load_yaml_reader(yaml_file)

        def remove_yaml_filter(data):

            # Just some checking in the edge case where a user is simultaneously loading another file...
            if data.name != os.path.basename(filename).split('.')[0]:
                return

            # io_registry._readers.pop((yaml_filter, Spectrum1DRef))
            # io_registry._identifiers.pop((yaml_filter, Spectrum1DRef))

            # dispatch.unregister_listener("on_added_data", remove_yaml_filter)

        # dispatch.register_listener("on_added_data", remove_yaml_filter)
        #
        # # Emit signal to indicate that file should be read
        # dispatch.on_file_read.emit(file_name=filename,
        #                            file_filter=yaml_filter)


if __name__ == "__main__":

    app = QApplication([])
    dialog = FITSImportWizard(simplify_arrays(parse_fits(sys.argv[1])))
    dialog.exec_()
