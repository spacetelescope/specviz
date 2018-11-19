import shutil
import urllib.request
import os

from specviz.plugins.loader_wizard.loader_wizard import (ASCIIImportWizard,
                                                         simplify_arrays,
                                                         parse_ascii)


def test_loader_wizard(tmpdir, qtbot):

    tmpfile = str(tmpdir.join('example.txt'))

    data_url = 'https://stsci.app.box.com/index.php?rm=box_download_shared_file' \
               '&shared_name=zz2vgbreuzhjtel0d5u96r30oofolod7&file_id=f_345743002081'
    with urllib.request.urlopen(data_url) as response:
        with open(tmpfile, 'wb') as handle:
            shutil.copyfileobj(response, handle)

    # Read in table from temp file and load wizard widget
    arrays = simplify_arrays(parse_ascii(tmpfile, 'format = "ascii"'))
    widget = ASCIIImportWizard(tmpfile, arrays)

    qtbot.addWidget(widget)

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

