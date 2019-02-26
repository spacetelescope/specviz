import os

from astropy.tests.helper import assert_quantity_allclose

from specutils import Spectrum1D


def test_create_filters(specviz_gui):

    workspace = specviz_gui.add_workspace()
    filters, loader_name_map = workspace._create_loader_filters()

    # Simple sanity test to make sure regression was removed
    assert filters[0] == 'Auto (*)'
    assert loader_name_map['Auto (*)'] is None


def test_export_data(specviz_gui, tmpdir):

    fname = str(tmpdir.join('export.ecsv'))

    workspace = specviz_gui._workspaces[0]
    data_item = workspace.current_item
    workspace.export_data_item(data_item, fname, '*.ecsv')

    assert os.path.isfile(fname)

    exported = Spectrum1D.read(fname, format='ECSV')
    original = data_item.data_item.spectrum

    assert_quantity_allclose(exported.flux, original.flux)
    assert_quantity_allclose(exported.spectral_axis, original.spectral_axis)
    if original.uncertainty is None:
        assert exported.uncertainty is None
    else:
        assert_quantity_allclose(exported.uncertainty, original.uncertainty)
