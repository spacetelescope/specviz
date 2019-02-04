from numbers import Number

import numpy as np
from astropy import units as u
from astropy.wcs import WCS
from astropy.table import Table

from qtpy.QtWidgets import QMessageBox

UNIT_FIXES = {
    'COUNTS SEC-1 METER-1': u.count / u.s / u.m,
    'MICRONS': u.micron,
    'HZ': u.Hz,
    'Angstroms': u.Angstrom,
    'ergs/cm^2/s': u.erg / u.cm ** 2 / u.s,
    '(COUNTS SEC-1 METER-1)**2': (u.count / u.s / u.m) ** 2
}


def parse_unit(unit):
    """
    Parse unit input into an :class:`Astropy.units.Unit` object.


    Parameters
    ----------
    unit : str or :class:`Astropy.units.Unit`
        Input unit. If not a string, may already be in :class:`Astropy.units.Unit`.

    Returns
    -------
    : :class:`Astropy.units.Unit`
        The interpreted Astropy unit.
    """
    if not isinstance(unit, u.Unit):

        if isinstance(unit, u.UnrecognizedUnit):
            unit = unit.to_string()

        unit = UNIT_FIXES.get(unit, unit)
        unit = u.Unit(unit, parse_strict='silent')

    return unit


def _parse(filename, table=None):

    dataset = {}

    if table is not None:
        for column_name in table.columns:

            data = table[column_name].data

            # If the parsed data is of type string, ignore this column
            if not isinstance(data.flatten()[0], Number):
                continue

            if table[column_name].unit is None:
                unit = None
            else:
                unit = parse_unit(table[column_name].unit)

            dataset[column_name] = {'data': data.flatten(),
                                    'ndim': data.ndim,
                                    'shape': data.shape,
                                    'unit': unit,
                                    'index': 0}

    return dataset


def parse_ascii(filename, read_input=None):
    """
    Read file into `Astropy.table.Table` using `Table.read`.  Additional
    if some read_input is provided, split this into input parameters
    for the `Table.read` call.

    Parameters
    ----------
    filename: str
        Input table filename.
    read_input: str
        Input string containing input parameters.

    Returns
    -------
    : dict
        Parsed dataset dictionary.
    """
    if read_input == None:
        try:
            itable = Table.read(filename)
        except Exception as e:
            itable = None

    else:
        # split parameter string out into dictionary
        try:
            kwargs = {a.split("=")[0].strip() : a.split("=")[1].strip().strip('"').strip("'")
                  for a in read_input.split(",")}
            itable = Table.read(filename, **kwargs)
        except Exception as e:
            QMessageBox.critical(None, "Table Read Error", "Couldn't read file "
                                                           "into table with "
                                                           "given parameters.")
            itable = None

    return _parse(filename, itable)


def simplify_arrays(dataset):
    """
    Loop through datasets and reduce length zero axes.

    Parameters
    ----------
    dataset : dict
        Dictionary containing dataset information.

    Returns
    -------
    : dataset
        Reduced dataset dictionary.

    """
    for component in dataset.values():
        if isinstance(component['data'], WCS):
            continue
        shape = component['data'].shape
        if np.product(shape) == np.max(shape):
            component['data'] = component['data'].ravel()
            component['ndim'] = component['data'].ndim
            component['shape'] = component['data'].shape
    return dataset


if __name__ == "__main__":

    import glob

    for filename in glob.glob('spectra/3000030_1_sed.fits'):
        print('-' * 72)
        print(filename)
        print('-' * 72)
        hdus = parse_ascii(filename)
        hdus = simplify_arrays(hdus)
        for name in hdus:
            print('HDU:', name)
            hdu = hdus[name]
            for array_name in hdu:
                array = hdu[array_name]
                print('  Array:', array_name)
                print('    data:', array['data'].min(), array['data'].max())
                print('    ndim:', array['ndim'])
                print('    shape:', array['shape'])
                print('    unit:', array['unit'])
