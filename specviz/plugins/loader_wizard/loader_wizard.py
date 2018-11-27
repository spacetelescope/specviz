# The import wizard is implemented in a way that is not specific to any given
# file format, but instead has the concept that a file can include one or more
# datasets, and a dataset can include one or more components. In the case of
# a FITS file, the datasets are HDUs, and components can be columns, standalone
# components (in the case of a Primary or ImageHDU), or spectral WCS for
# example.

import importlib
import os
import sys
import tempfile
import uuid
from collections import OrderedDict

import numpy as np
import pyqtgraph as pg
import yaml
from astropy import units as u
from astropy.io import registry
from astropy.wcs import WCS
from qtpy import compat
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont, QIcon
from qtpy.QtWidgets import (QApplication, QDialog, QMessageBox, QPlainTextEdit,
                            QPushButton, QVBoxLayout, QWidget)
from qtpy.uic import loadUi

from specutils import Spectrum1D

from ...core.plugin import plugin
from .parse_initial_file import parse_ascii, simplify_arrays


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
              u.erg / u.cm**2 / u.s / u.um, u.erg / u.cm**2 / u.s / u.Angstrom,
              u.erg / u.cm**2 / u.s]


class OutputPreviewWidget(QWidget):
    """
    A .py preview widget that appears as a drawer on the side of the main
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

    def __init__(self, dataset, combo_component, combo_units=None,
                 valid_units=None, custom_units=None, label_status=None, allow_wcs=True):

        if dataset == {}:
            self.dataset = None
        else:
            self.dataset = dataset
        self.combo_component = combo_component
        self.combo_units = combo_units
        self.valid_units = valid_units
        self.custom_units = custom_units
        self.label_status = label_status
        self.allow_wcs = allow_wcs

        # Attempt to initialize combo box of dataset.
        self._set_units()

        # Set up callbacks for various events

        # flag
        #self.combo_dataset.currentIndexChanged.connect(self._dataset_changed)
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

    def dataset_update(self, new_dataset, is_enabled=True):
        self.dataset = new_dataset
        self._dataset_changed(is_enabled=is_enabled)
        self._set_units()

    def _set_units(self):

        if self.combo_units is not None:
            self.combo_units.clear()
            for unit in self.valid_units:
                self.combo_units.addItem(str(unit), userData=unit)
            self.combo_units.addItem('Custom', userData='Custom')

    def _dataset_changed(self, event=None, is_enabled=True):

        if self.dataset is None:
            self.combo_component.setCurrentIndex(-1)
            return

        self.combo_component.blockSignals(True)
        self.combo_component.clear()
        # might need to change this
        self.combo_component.setEnabled(is_enabled)
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

        if self.dataset is None or self.dataset == {}:
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
    A wizard to help with importing spectra from files. We may not need
    separate parent and children classes. Retaining this structure until we
    make some final design desicions about the loader wizard.
    """

    dataset_label = 'Dataset'

    def __init__(self, filename, dataset, parent=None):

        super(BaseImportWizard, self).__init__(parent=parent)

        self.filename = filename
        self.dataset = dataset
        self.new_loader_dict = OrderedDict()

        self.ui = loadUi(os.path.abspath(
               os.path.join(os.path.dirname(__file__), "loader_wizard.ui")), self)

        self.helper_disp = ComponentHelper(self.dataset,
                                           self.ui.combo_dispersion_component,
                                           self.ui.combo_dispersion_units,
                                           DISPERSION_UNITS,
                                           self.ui.value_dispersion_units,
                                           self.ui.label_dispersion_status)

        self.helper_data = ComponentHelper(self.dataset,
                                           self.ui.combo_data_component,
                                           self.ui.combo_data_units,
                                           DATA_UNITS,
                                           self.ui.value_data_units,
                                           self.ui.label_data_status,
                                           allow_wcs=False)

        self.helper_unce = ComponentHelper(self.dataset,
                                           self.ui.combo_uncertainty_component,
                                           allow_wcs=False)

        self.helper_mask = ComponentHelper(self.dataset,
                                           self.ui.combo_mask_component,
                                           allow_wcs=False)

        self.output_preview = OutputPreviewWidget(self)
        self.output_preview.hide()
        self.ui.button_yaml.clicked.connect(self._toggle_output_preview)

        self.ui.button_ok.clicked.connect(self.accept)

        self.ui.combo_uncertainty_type.addItem('Standard Deviation', userData='std')
        self.ui.combo_uncertainty_type.addItem('Inverse Variance', userData='ivar')

        # Set callback for line_table_read callback
        self.ui.button_refresh_data.clicked.connect(self._update_data)

        # Set the astropy.table.Table.read() comboBox and other ui elements
        self.ui.line_table_read.text()

        pg.setConfigOption('foreground', 'k')

        self.plot_widget = pg.PlotWidget(title="Spectrum preview",
                                         parent=self,
                                         background=None)
        self.layout_preview.addWidget(self.plot_widget)

        self.ui.label_unit_status.setText('')

        self.ui.bool_uncertainties.setChecked(False)
        self.set_uncertainties_enabled(False)
        self.ui.bool_uncertainties.toggled.connect(self.set_uncertainties_enabled)

        self.ui.bool_mask.blockSignals(True)
        self.ui.combo_bit_mask_definition.blockSignals(True)
        self.ui.combo_mask_component.blockSignals(True)
        self.ui.bool_mask.setEnabled(False)
        self.ui.combo_bit_mask_definition.setEnabled(False)
        self.ui.combo_mask_component.setEnabled(False)

        ## will implement this in the future
        # self.ui.bool_mask.setChecked(False)
        # self.set_mask_enabled(False)
        # # self.ui.bool_mask.toggled.connect(self.set_mask_enabled)
        #
        # self.ui.combo_bit_mask_definition.addItem('Custom', userData='custom')
        # self.ui.combo_bit_mask_definition.addItem('SDSS', userData='sdss')
        # self.ui.combo_bit_mask_definition.addItem('JWST', userData='jwst')

        ## so for now we will set them to invisible
        self.ui.label_4m.setVisible(False)
        self.ui.bool_mask.setVisible(False)
        self.ui.label_mask_component.setVisible(False)
        self.ui.combo_mask_component.setVisible(False)
        self.ui.label_mask_definition.setVisible(False)
        self.ui.combo_bit_mask_definition.setVisible(False)

        self.ui.loader_name.textChanged.connect(self._clear_loader_name_status)
        self.ui.value_dispersion_units.textChanged.connect(self._clear_unit_status)
        self.ui.value_data_units.textChanged.connect(self._clear_unit_status)

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

        self.combo_uncertainty_component.blockSignals(not enabled)
        self.combo_uncertainty_type.blockSignals(not enabled)

        self.combo_uncertainty_component.setEnabled(enabled)
        self.combo_uncertainty_type.setEnabled(enabled)

        self._update_preview()

    def set_mask_enabled(self, enabled):

        self.combo_mask_component.blockSignals(not enabled)
        self.combo_bit_mask_definition.blockSignals(not enabled)

        self.combo_mask_component.setEnabled(enabled)
        self.combo_bit_mask_definition.setEnabled(enabled)


    @property
    def uncertainties_enabled(self):
        return self.bool_uncertainties.isChecked()

    def accept(self, event=None):
        super(BaseImportWizard, self).accept()

    def _update_data(self):

        self.dataset = simplify_arrays(parse_ascii(self.filename,
                                                    self.ui.line_table_read.text()))
        self.helper_disp.dataset_update(self.dataset)
        self.helper_data.dataset_update(self.dataset)
        self.helper_unce.dataset_update(self.dataset, is_enabled= self.ui.bool_uncertainties.isChecked())
        # implementing in future
        # self.helper_mask.dataset_update(self.dataset, is_enabled= self.ui.bool_mask.isChecked())


    def _update_preview(self, event=None):

        self.plot_widget.clear()

        x = self.helper_disp.data
        y = self.helper_data.data
        if self.ui.bool_uncertainties.isChecked():
            yerr = self.helper_unce.data
        else:
            yerr = None

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

        template_path = self.get_template()

        with open(template_path, 'r') as f:
            filled_template = f.read().format(**self.new_loader_dict)

        return filled_template

    def _clear_loader_name_status(self):
        self.ui.label_loader_name_status.setText('')
        self.ui.label_loader_name_status.setStyleSheet('')

    def _clear_unit_status(self):
        self.ui.label_unit_status.setText('')
        self.ui.label_unit_status.setStyleSheet('')

    def save_loader_check(self):
        if (self.helper_disp.combo_units.currentText() == "Custom" and self.helper_disp.label_status.text() != 'Valid units') or \
                (self.helper_data.combo_units.currentText() == "Custom" and self.helper_data.label_status.text() != 'Valid units'):
            self.ui.label_unit_status.setText('Found invalid units')
            self.ui.label_unit_status.setStyleSheet('color: red')
            return False

        if self.ui.loader_name.text() == "":
            self.ui.label_loader_name_status.setText('Enter a name for the loader')
            self.ui.label_loader_name_status.setStyleSheet('color: red')
            return False

        return True


    def save_loader_script(self, event=None, output_directory=None):
        """
        oputput_directory parameter is strictly for use in tests.
        """

        if not self.save_loader_check():
            return

        specutils_dir = os.path.join(os.path.expanduser('~'), '.specutils')

        if not os.path.exists(specutils_dir):
            os.mkdir(specutils_dir)

        loader_name = self.ui.loader_name.text()

        # If the loader name already exists in the registry, raise a warning
        # and ask the user to pick another name
        if loader_name in registry.get_formats(Spectrum1D, 'Read')['Format']:
            message_box = QMessageBox()
            message_box.setText("Loader name already exists.")
            message_box.setIcon(QMessageBox.Critical)
            message_box.setInformativeText(
                "A loader with the name '{}' already exists in the registry. "
                "Please choose a different name.".format(loader_name))

            message_box.exec()
            return

        out_path = os.path.join(specutils_dir, loader_name)

        filename = compat.getsavefilename(parent=self,
                                          caption='Export loader to .py file',
                                          basedir=out_path)[0]
        if filename == '':
            return

        self.save_register_new_loader(filename)

    def save_register_new_loader(self, filename):
        filename = "{}.py".format(filename) if not filename.endswith(".py") else filename

        string = self.as_new_loader()

        with open(filename, 'w') as f:
            f.write(string)

        # If a loader by this name exists, delete it
        if self.new_loader_dict['name'] in registry.get_formats()['Format']:
            registry.unregister_reader(self.new_loader_dict['name'], Spectrum1D)
            registry.unregister_identifier(self.new_loader_dict['name'], Spectrum1D)

        # Add new loader to registry
        spec = importlib.util.spec_from_file_location(os.path.basename(filename)[:-3], filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        message_box = QMessageBox()
        message_box.setText("Loader saved successful.")
        message_box.setIcon(QMessageBox.Information)
        message_box.setInformativeText("Custom loader was saved successfully.")

        message_box.exec()


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


class ASCIIImportWizard(BaseImportWizard):
    """
    We have simpliefied the loader wizard to using Table.read() for
    any potential loader.  We may want to expand this, but if not, it can
    be merged into it's parent class.
    """

    dataset_label = 'Table'

    def as_new_loader_dict(self, name=None):
        """
        Convert the current configuration to a dictionary
        that can then be serialized to a Python file
        """
        self.new_loader_dict['name'] = name or self.ui.loader_name.text()

        if self.ui.line_table_read.text() == "":
            self.new_loader_dict['table_read_kwargs'] = ''
        else:
            self.new_loader_dict['table_read_kwargs'] = ", "+self.ui.line_table_read.text()

        self.new_loader_dispersion()

        self.new_loader_data()

        self.new_loader_uncertainty()

        ## will implement this in the future
        # if self.ui.bool_mask.isChecked():
        #     # if going to use this, might need to change this to single
        #     # dict items
        #     self.new_loader_dict['mask'] = OrderedDict()
        #     self.new_loader_dict['mask']['hdu'] = self.helper_mask.hdu_index
        #     self.new_loader_dict['mask']['col'] = self.helper_mask.component_name
        #     definition = self.ui.combo_bit_mask_definition.currentData()
        #     if definition != 'custom':
        #         self.new_loader_dict['mask']['definition'] = definition

        self.new_loader_dict['meta_author'] = 'Wizard'

        self.add_extension()


    def add_extension(self):
        self.new_loader_dict['extension'] = ['dat']


    def get_template(self):
        template_string = "new_loader_"

        if "uncertainty_hdu" in self.new_loader_dict.keys():
            if self.new_loader_dict['uncertainty_type'] == 'std':
                template_string += "uncer_stddev_"

            else:
                template_string += "uncer_ivar_"

        template_string += "py.tmpl"

        template_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), ".", template_string))

        return template_path


@plugin("Loader Wizard")
class LoaderWizard(QDialog):
    @plugin.tool_bar("Loader Wizard", icon=QIcon(":/icons/012-file.svg"), location=0)
    def open_wizard(self):

        filters = ["FITS, ECSV, text (*.fits *.ecsv *.dat *.txt *.*)"]
        filename, file_filter = compat.getopenfilename(filters=";;".join(filters))

        if filename == '':
            return

        dialog = ASCIIImportWizard(filename,
                                   simplify_arrays(parse_ascii(filename, read_input=None)))


        val = dialog.exec_()

        if val == 0:
            return

        # Make temporary YAML file
        yaml_file = tempfile.mktemp()
        with open(yaml_file, 'w') as f:
            f.write(dialog.as_new_loader(name=str(uuid.uuid4())))




if __name__ == "__main__":

    app = QApplication([])
    dialog = FITSImportWizard(simplify_arrays(parse_ascii(sys.argv[1])))
    dialog.exec_()
