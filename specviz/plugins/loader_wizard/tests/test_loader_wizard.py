import os
import shutil
import urllib.request

from qtpy.QtWidgets import QMessageBox
from qtpy.QtCore import Qt

from specviz.plugins.loader_wizard.loader_wizard import (ASCIIImportWizard, parse_ascii,
                                            simplify_arrays)


def test_loader_wizard(tmpdir, qtbot, monkeypatch):
    # Monkeypatch the QMessageBox widget so that it doesn't block the test
    # progression. In this case, accept the information dialog indicating that
    # a loader has been saved.
    monkeypatch.setattr(QMessageBox, "information", lambda *args: QMessageBox.Ok)

    tmpfile = str(tmpdir.join('example.txt'))

    data_url = 'https://stsci.app.box.com/index.php?rm=box_download_shared_file' \
               '&shared_name=zz2vgbreuzhjtel0d5u96r30oofolod7&file_id=f_345743002081'
    with urllib.request.urlopen(data_url) as response:
        with open(tmpfile, 'wb') as handle:
            shutil.copyfileobj(response, handle)

    # Read in table from temp file and load wizard widget
    arrays = simplify_arrays(parse_ascii(tmpfile))
    widget = ASCIIImportWizard(tmpfile, arrays)

    qtbot.addWidget(widget)

    widget.line_table_read.setText('format="ascii"')
    widget._update_data()

    # set units and column choices
    widget.combo_dispersion_units.setCurrentIndex(0)
    widget.combo_data_component.setCurrentIndex(1)
    widget.combo_data_units.setCurrentIndex(2)

    # Set loader name and run save check
    widget.loader_name.setText("loadertest")
    assert widget.save_loader_check()

    filename = os.path.join(tmpdir, "loader_temp.py")

    widget.save_register_new_loader(filename)

    with open(filename) as f:
        created_out = f.read()

    # Not the nicest text block, but better then putting the comparison
    # file in git.
    expected_out = """import os

from astropy.table import Table
from astropy.units import Unit

from specutils.io.registers import data_loader
from specutils import Spectrum1D


@data_loader(label="loadertest")
def simple_generic_loader(file_name):
    # Use name of the file for the spectra object that's created
    # when the data is loaded.
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]

    ast_table = Table.read(file_name, format="ascii")

    flux = ast_table["flux"].flatten()
    wavelength = ast_table["wavelength"].flatten()

    # Set units
    unit = Unit("Jy")
    disp_unit = Unit("Angstrom")

    # A new spectrum object is returned, which specviz understands
    return Spectrum1D(spectral_axis=wavelength*disp_unit, flux=flux*unit)
"""

    assert created_out == expected_out
