import numpy as np

from astropy.io import ascii
from astropy.table import Table

from . import parse_fits


def _parse(filename, table):

    # Here we adopt the same data structures used in the handling
    # of FITS files, replacing the HDUs by datasets. An ECSV table
    # will typically contain only one dataset.

    parsed_datasets = {}
    dataset = {}

    for column_name in table.columns:

        if table[column_name].unit is None:
            unit = None
        else:
            unit = parse_fits.parse_unit(table[column_name].unit)

        data = table[column_name].data

        # If the parsed data is of type string, ignore this column
        if isinstance(data, np.chararray):
            continue

        dataset[column_name] = {'data': data.flatten(),
                                'ndim': data.ndim,
                                'shape': data.shape,
                                'unit': unit,
                                'index': 0}

    parsed_datasets[filename] = dataset

    return parsed_datasets


def parse_ecsv(filename):

    table = Table.read(filename, format='ascii.ecsv')

    return _parse(filename, table)


def parse_ascii(filename):

    table = ascii.read(filename)

    return _parse(filename, table)

