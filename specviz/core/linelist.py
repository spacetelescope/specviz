"""
Emission/Absorption Line list utilities
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import glob
import yaml

import numpy as np

from astropy.io import ascii
from astropy.table import Table, vstack


__all__ = [
    'LineList',
    'ingest',
]

FORMAT = 'line_list'
COLUMN_NAME = 'name'
COLUMN_START = 'start'
COLUMN_END = 'end'
WAVELENGTH_COLUMN = 'Wavelength'
ID_COLUMN = 'Line ID'
UNITS_COLUMN = 'units'
COLOR_COLUMN = 'Color'


def ingest(range):
    """
    Returns a list with LineList instances.

    Each original list is stripped out of lines that lie outside the
    wavelength range.

    Parameters
    ----------
    range:
        The wavelength range of interest.

    Returns
    -------
    [LineList, ...]
        The list of linelists found.

    Notes
    -----
    Lets skip the file dialog business. For now, we look
    for line lists and their accompanying YAML files in
    one single place. We also restrict our search for
    ascii line lists whose file names end in .txt
    """
    linelist_path = os.path.dirname(os.path.abspath(__file__))
    linelist_path +=  '/../data/linelists/'
    yaml_paths = glob.glob(linelist_path + '*.yaml')
    linelists = []

    for yaml_filename in yaml_paths:

        loader = yaml.load(open(yaml_filename, 'r'))

        linelist_fullname = linelist_path + loader.filename

        linelist = LineList.read_list(linelist_fullname, loader)
        # linelist = linelist.extract_range(range)

        linelists.append(linelist)

    return linelists


# Inheriting from QTable somehow makes this class incompatible
# with the registry machinery in astropy.

class LineList(Table):
    """
    A list of emission/absorption lines

    Parameters
    ----------
    table: `~astropy.table.Table`
        If specified, a table to initialize from.

    name: str
        The name of the list.

    masked: bool
        If true, a masked table is used.
    """

    def __init__(self, table=None, name=None, masked=None):
        Table.__init__(self, data=table, masked=masked)

        self.name = name

        # We have to carry internally a raw reference to the
        # table data so as to be able to use vstack() to perform
        # merging. This shouldn't be a problem as long as the
        # LineList instance is regarded as immutable. Which it
        # should be anyways.

        self._table = table

        # each list has a color property associated to it
        self.color = None

    @classmethod
    def read_list(self, filename, yaml_loader):
        names_list = []
        start_list = []
        end_list = []
        units_list = []
        for k in range(len((yaml_loader.columns))):
            name = yaml_loader.columns[k][COLUMN_NAME]
            names_list.append(name)

            start = yaml_loader.columns[k][COLUMN_START]
            end = yaml_loader.columns[k][COLUMN_END]
            start_list.append(start)
            end_list.append(end)

            if UNITS_COLUMN in yaml_loader.columns[k]:
                units = yaml_loader.columns[k][UNITS_COLUMN]
            else:
                units = ''
            units_list.append(units)

        tab = ascii.read(filename, format = yaml_loader.format,
                         names = names_list,
                         col_starts = start_list,
                         col_ends = end_list)

        for k, colname in enumerate(tab.columns):
            tab[colname].unit = units_list[k]

            # some line lists have a 'Reference' column that is
            # wrongly read as type int. Must be str instead,
            # otherwise an error is raised when merging.
            if colname in ['Reference']:
                tab[colname] = tab[colname].astype(str)

        # The table name (for e.g. display purposes)
        # is taken from the 'name' element in the
        # YAML file descriptor.

        return LineList(tab, yaml_loader.name)

    @classmethod
    def merge(cls, lists, target_units):
        """
        Executes a 'vstack' of all input lists, and
        then sorts the result by the wavelength column.

        Parameters
        ----------
        lists: [LineList, ...]
            list of LineList instances
        target_units: Units
            units to which all lines from all tables
            must be converted to.

        Returns
        -------
        LineList
            merged line list
        """
        tables = []
        for linelist in lists:

            # Note that vstack operates on Table instances but
            # not on LineList instances. So we refer directly
            # to the raw Table instances.

            internal_table = linelist._table
            internal_table[WAVELENGTH_COLUMN].convert_unit_to(target_units)

            # add a column to hold the color property
            color_array = np.full(len(internal_table[WAVELENGTH_COLUMN]), linelist.color)
            internal_table[COLOR_COLUMN] = color_array

            tables.append(internal_table)

        merged_table = vstack(tables)

        merged_table.sort(WAVELENGTH_COLUMN)

        return cls(merged_table, "Merged")

    def extract_range(self, wrange):
        """
        Builds a LineList instance out of self, with
        the subset of lines that fall within the
        wavelength range defined by 'wmin' and 'wmax'

        Parameters
        ----------
        wrange: (float, float)
            minimum and maximum wavelength of the wavelength range

        Returns
        -------
        LineList
            line list with subset of lines
        """
        wavelengths = self[WAVELENGTH_COLUMN].quantity

        wmin = wrange[0]
        wmax = wrange[1]

        # convert wavelenghts in line list to whatever
        # units the wavelength range is expressed in.
        new_wavelengths = wavelengths.to(wmin.unit)

        # 'indices' points to rows with wavelength values
        # that lie outside the wavelength range.
        indices_to_remove = np.where((new_wavelengths.value < wmin.value) |
                                     (new_wavelengths.value > wmax.value))

        return self._remove_lines(indices_to_remove)

    def extract_rows(self, indices):
        """
        Builds a LineList instance out of self, with
        the subset of lines pointed by 'indices'

        Parameters
        ----------
        indices: [QModelIndex, ...]
            List of QModelIndex instances to extract from.

        Returns
        -------
        LineList
            line list with subset of lines
        """
        row_indices = []
        for index in indices:
            row_indices.append(index.row())

        line_indices = []
        for index in range(len(self.columns[0])):
            line_indices.append(index)

        indices_to_remove = list(
            filter(lambda x: x not in row_indices, line_indices)
        )

        return self._remove_lines(indices_to_remove)

    def _remove_lines(self, indices_to_remove):
        """
        Makes a copy of self and removes
        unwanted lines from the copy.

        Parameters
        ----------
        indices_to_remove: [int, ...]
            List of row numbers to remove

        Returns
        -------
        LineList:
            A new copy of the `LineList` with the rows removed.
        """
        table = Table(self)

        table.remove_rows(indices_to_remove)

        result = LineList(table, self.name)

        return result

    def setColor(self, color):
        self.color = color
