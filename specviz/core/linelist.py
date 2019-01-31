"""

Line list utilities

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import glob
import yaml

import numpy as np

from astropy.io import ascii
from astropy.table import Table, vstack
from astropy import constants
from astropy import units as u
from astropy.units.core import UnitConversionError


__all__ = [
    'get_from_file',
    'get_from_cache',
    'ingest',
    'populate_linelists_cache',
    'descriptions',
    'LineList',
]

# yaml specs
FORMAT = 'line_list'
COLUMN_NAME = 'name'
COLUMN_START = 'start'
COLUMN_END = 'end'
WAVELENGTH_COLUMN = 'Wavelength'
ERROR_COLUMN = 'Error'
ID_COLUMN = 'Species'
UNITS_COLUMN = 'units'
TOOLTIP_COLUMN = 'tooltip'

# plotting helpers
REDSHIFTED_WAVELENGTH_COLUMN = 'z_wavelength'
COLOR_COLUMN = 'color'
HEIGHT_COLUMN = 'height'
MARKER_COLUMN = 'marker'
DEFAULT_HEIGHT = 0.75

# columns to remove when exporting the plotted lines
columns_to_remove = [REDSHIFTED_WAVELENGTH_COLUMN, COLOR_COLUMN, HEIGHT_COLUMN, MARKER_COLUMN]

_linelists_cache = []


def get_from_file(filename, linelist_path=None):
    """
    Create a line list based on the definition in a file.

    Parameters
    ----------
    filename : str
        The filename of the definition file for the line list. This can either
        be a YAML file with a definition of the line list, or an ECSV with an
        actual line list.
    linelist_path : str, optional
        If `filename` points to a YAML file, this gives the directory in which
        the actual line lists are stored

    Returns
    -------
    `~specviz.core.linelist.LineList` or `None`
        The line list - if the file is neither a YAML or ECSV file, `None` is
        returned.
    """
    if filename.endswith('.yaml'):

        if linelist_path is None:
            raise ValueError("linelist_path is required")

        yaml_object = yaml.load(open(filename, 'r'))
        linelist_fullname = os.path.join(linelist_path, yaml_object['filename'])

        return LineList.read_list(linelist_fullname, yaml_object)

    elif filename.endswith('.ecsv'):
        table = Table.read(filename, format='ascii.ecsv')

        linelist = LineList(table, name=os.path.split(filename)[1])
        _linelists_cache.append(linelist)

        return linelist

    else:
        return None


# This should be called at the appropriate time when starting the
# app, so the lists are cached for speedier access later on.
def populate_linelists_cache():
    """
    Read in all the available line lists packaged with specviz into a cache.
    """
    # we could benefit from a threaded approach here. But I couldn't
    # see the benefits, since the reading of even the largest line
    # list files takes a fraction of a second at most.
    linelist_path = os.path.dirname(os.path.abspath(__file__))
    linelist_path = os.path.join(linelist_path, '..', 'data', 'linelists')
    yaml_paths = glob.glob(linelist_path + '*.yaml')

    for yaml_filename in yaml_paths:
        linelist = get_from_file(linelist_path, yaml_filename)
        _linelists_cache.append(linelist)


def get_from_cache(index):
    """
    Get the n-th `~specviz.core.linelist.LineList` from the cache.

    Parameters
    ----------
    index : int
        The line list to get from the cache

    Returns
    -------
    `~specviz.core.linelist.LineList` or `None`
        The requested line list

    """
    return _linelists_cache[index]


def ingest(range):
    """
    Returns a list with `~specviz.core.linelist.LineList` instances containing
    only entries that fall inside the specified wavelength range.

    Parameters
    ----------
    range : a tuple of `~astropy.units.Quantity`
        The wavelength range of interest.

    Returns
    -------
    [LineList, ...]
        The list of `~specviz.core.linelist.LineList` instances
    """
    result = []
    for linelist in _linelists_cache:
        try:
            ll = linelist.extract_range(range)
            result.append(ll)
        except UnitConversionError as err:
            pass

    return result


def descriptions():
    """
    Returns a list with strings containing a description of each line list in
    the cache.

    Returns
    -------
    list
        The list of strings.
    """
    result = []
    for linelist in _linelists_cache:

        desc = linelist.name
        nlines = len(linelist[WAVELENGTH_COLUMN])
        w1 = linelist.wmin
        w2 = linelist.wmax
        units = linelist[WAVELENGTH_COLUMN].unit

        description = '{:15}  ({:>d},  [ {:.2f} - {:.2f} ] {})'.format(desc, nlines, w1, w2, units)

        result.append(description)

    return result


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
        If `True`, a masked table is used.
    """

    def __init__(self, table=None, tooltips=None, name=None, masked=None):
        Table.__init__(self, data=table, masked=masked)

        self.name = name

        # We have to carry internally a raw reference to the
        # table data so as to be able to use vstack() to perform
        # merging. This shouldn't be a problem as long as the
        # LineList instance is regarded as immutable. Which it
        # should be anyways.

        self._table = table

        # each list has associated color, height, and redshift attributes
        self.color = None
        self.height = DEFAULT_HEIGHT
        self.redshift = 0.
        self. z_units = 'z'

        if len(table[WAVELENGTH_COLUMN].data):
            self.wmin = table[WAVELENGTH_COLUMN].data.min()
            self.wmax = table[WAVELENGTH_COLUMN].data.max()
        else:
            self.wmin = self.wmax = None

        # A line list (but not the underlying table) can have
        # tool tips associated to each column.
        self.tooltips = tooltips

    @property
    def table(self):
        """
        The underlying `~astropy.table.Table` object.
        """
        return self._table

    @classmethod
    def read_list(cls, filename, yaml_object):
        """
        Read in a line list from a file.

        Parameters
        ----------
        filename : str
            The file containing the line list to read in.
        yaml_object : dict
            A dictionary read in from a YAML file providing a description of
            how to read in the line list.

        Returns
        -------
        `~specviz.core.linelist.LineList`
            The resulting line list.
        """
        names_list = []
        start_list = []
        end_list = []
        units_list = []
        tooltips_list = []
        for k in range(len((yaml_object['columns']))):
            name = yaml_object['columns'][k][COLUMN_NAME]
            names_list.append(name)

            start = yaml_object['columns'][k][COLUMN_START]
            end = yaml_object['columns'][k][COLUMN_END]
            start_list.append(start)
            end_list.append(end)

            units = ''
            if UNITS_COLUMN in yaml_object['columns'][k]:
                units = yaml_object['columns'][k][UNITS_COLUMN]
            units_list.append(units)

            tooltip = ''
            if TOOLTIP_COLUMN in yaml_object['columns'][k]:
                tooltip = yaml_object['columns'][k][TOOLTIP_COLUMN]
            tooltips_list.append(tooltip)

        tab = ascii.read(filename, format=yaml_object['format'],
                         names=names_list,
                         col_starts=start_list,
                         col_ends=end_list)

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

        return cls(tab, tooltips=tooltips_list, name=yaml_object['name'])

    @classmethod
    def merge(cls, lists, target_units):
        """
        Executes a 'vstack' of all input lists, and then sorts the result by the
        wavelength column.

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
            internal_table[WAVELENGTH_COLUMN].convert_unit_to(target_units, equivalencies=u.spectral())

            # add columns to hold color and height attributes
            color_array = np.full(len(internal_table[WAVELENGTH_COLUMN]), linelist.color)
            internal_table[COLOR_COLUMN] = color_array
            height_array = np.full(len(internal_table[WAVELENGTH_COLUMN]), linelist.height)
            internal_table[HEIGHT_COLUMN] = height_array

            # add column to hold redshifted wavelength
            f = 1. + linelist.redshift
            if linelist.z_units == 'km/s':
                f = 1. + linelist.redshift / constants.c.value * 1000.
            z_wavelength = internal_table[WAVELENGTH_COLUMN] * f
            internal_table[REDSHIFTED_WAVELENGTH_COLUMN] = z_wavelength

            # add column to hold plot markers
            marker_array = np.full(len(internal_table[WAVELENGTH_COLUMN]), None)
            internal_table[MARKER_COLUMN] = marker_array

            tables.append(internal_table)

        merged_table = vstack(tables)

        merged_table.sort(WAVELENGTH_COLUMN)

        return cls(merged_table, "Merged")

    def extract_range(self, wrange):
        """
        Return a new `~specviz.core.linelist.LineList` containing the subset of
        lines that fall within the wavelength range defined by 'wmin' and
        'wmax'.

        REMOVED FOR NOW: The actual range is somewhat
        wider, to allow for radial velocity and redshift
        effects. The actual handling of this must wait
        until we get more detailed specs for the redshift
        functionality.

        Parameters
        ----------
        wrange: (`~astropy.units.Quantity`, `~astropy.units.Quantity`)
            Minimum and maximum wavelength to use to extract the lines.

        Returns
        -------
        `~specviz.core.linelist.LineList`
            line list with subset of lines
        """
        wavelengths = self[WAVELENGTH_COLUMN].quantity

        wmin = wrange[0]
        wmax = wrange[1]

        # convert wavelenghts in line list to whatever
        # units the wavelength range is expressed in.
        new_wavelengths = wavelengths.to(wmin.unit, equivalencies=u.spectral())

        # add some leeway at the short and long end points.
        # For now, we extend both ends by 10%. This might
        # be enough at the short end, but it remains to be
        # seen how this plays out when we add redshift
        # functionality to the app.
        #
        # REMOVING THIS FOR NOW.
        # wmin = wmin.value - wmin.value * 0.1
        # wmax = wmax.value + wmax.value * 0.1
        wmin = wmin.value
        wmax = wmax.value

        # 'indices' points to rows with wavelength values
        # that lie outside the wavelength range.
        indices_to_remove = np.where((new_wavelengths.value < wmin) |
                                     (new_wavelengths.value > wmax))

        # if using frequency units, the test above fails. We have to
        # test for the opposite condition then.
        if len(indices_to_remove[0]) == len(new_wavelengths):
            indices_to_remove = np.where((new_wavelengths.value > wmin) |
                                         (new_wavelengths.value < wmax))

        result = self._remove_lines(indices_to_remove)

        # new instance inherits the name from parent.
        result.name = self.name

        return result

    def extract_rows(self, indices):
        """
        Return a new `~specviz.core.linelist.LineList` containing the subset of
        lines determined by the specified indices.

        Parameters
        ----------
        indices: [QModelIndex, ...]
            List of QModelIndex instances to extract from.

        Returns
        -------
        `~specviz.core.linelist.LineList`
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
        Returns a copy of the line list without the specified indices.

        Parameters
        ----------
        indices_to_remove: [int, ...]
            List of row numbers to remove

        Returns
        -------
        `~specviz.core.linelist.LineList`
            A new copy of the `~specviz.core.linelist.LineList` with the rows removed.
        """
        table = Table(self)

        table.remove_rows(indices_to_remove)

        result = LineList(table, tooltips=self.tooltips, name=self.name)

        return result

    def setRedshift(self, redshift, z_units):
        """

        Parameters
        ----------
        redshift
        z_units
        """
        self.redshift = redshift
        self.z_units = z_units

    def setColor(self, color):
        """

        Parameters
        ----------
        color
        """
        self.color = color

    def setHeight(self, height):
        """

        Parameters
        ----------
        height
        """
        self.height = height
