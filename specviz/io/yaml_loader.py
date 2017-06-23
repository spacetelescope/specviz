"""This module contains functions that perform the actual data parsing."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import logging
import os

# THIRD-PARTY
import numpy as np
from astropy import units as u
from astropy.io import ascii, fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.nddata import StdDevUncertainty

# LOCAL
from specviz.core.data import Spectrum1DRef
from specviz.core import linelist
from specviz.core.linelist import LineList

__all__ = [
    'AsciiYamlRegister',
    'FitsYamlRegister',
    'LineListYamlRegister',
    'YamlRegister',
]

# Loader automatically falls back to these units for some cases
default_waveunit = u.Unit('Angstrom')
default_fluxunit = u.Unit('erg / (Angstrom cm2 s)')


class YamlRegister(object):
    """
    Class to encapsulate the IO registry information for a set of
    yaml-loaded attributes.
    """
    def __init__(self, reference):
        """
        Initialize this particular YamlRegister.

        Parameters
        ----------
        reference : dict-like
            The yaml reference object created by loading a yaml file.
        """
        self._reference = reference

    def identify(self, *args, **kwargs):
        return (isinstance(args[0], str) and
                args[0].lower().split('.')[-1] in self._reference.extension)

    def reader(self, filename, **kwargs):
        raise NotImplementedError()


# NOTE: This is used by both FITS and ASCII.
def _set_uncertainty(err_array, err_type):
    """Uncertainty is dictated by its type.

    Parameters
    ----------
    err_array : array
        Uncertainty values.

    err_type : {'ivar', 'std'}
        Inverse variance or standard deviation.

    Returns
    -------
    uncertainty : `~astropy.nddata.nduncertainty.StdDevUncertainty`
        Standard deviation uncertainty.

    """
    if err_type == 'ivar':
        err = np.sqrt(1.0 / err_array)
    else:  # 'std'
        err = err_array

    return StdDevUncertainty(err)


def _flux_unit_from_header(header, key='BUNIT'):
    """Get flux unit from header.

    Parameters
    ----------
    header : dict
        Extracted header.

    key : str
        Keyword name.

    Returns
    -------
    unit : `~astropy.units.core.Unit`
        Flux unit. This falls back to default flux unit if look-up failed.

    """
    unitname = header.get(key, default_fluxunit.to_string()).lower()

    # TODO: A more elegant way is to use astropy.units.def_unit()
    if unitname == 'electrons/s':
        unitname = 'electron/s'

    try:
        unit = u.Unit(unitname)
    except ValueError as e:
        unit = default_fluxunit
        logging.warning(str(e))

    return unit


def _read_table(hdu, col_idx=0):
    """Parse FITS table using Astropy first, but use brute force
    if the former fails.

    Astropy parsing is very good at extracting unit and mask, along
    with the data, if FITS table is formatted properly.
    Brute force guarantees the data but provides no unit nor mask.

    Parameters
    ----------
    hdu : obj
        HDU object.

    col_idx : int
        Column index to extract the data directly from HDU.
        This is only used if Astropy parsing fails.

    Returns
    -------
    tab : `~astropy.table.table.Table`
        Parsed table.

    """
    # Let Astropy parse the table for us.
    try:
        tab = Table.read(hdu, format='fits')
    # Build manually if we have to.
    except:
        tab = Table([hdu.data[col_idx].flatten()])

    return tab


def _read_table_column(tab, col_idx, to_unit=None, equivalencies=[]):
    """Read a given Astropy Table column.

    Parameters
    ----------
    tab : `~astropy.table.Table`
        FITS table parsed by Astropy.

    col_idx : int or str
        Column index or name

    to_unit : `~astropy.units.core.Unit` or `None`
        If given, convert data to this unit.

    equivalencies : list
        Astropy unit conversion equivalencies, if needed.
        This might be needed for some flux or wavelength conversions.

    Returns
    -------
    data : array
        1D array of the values.

    unit : `~astropy.units.core.Unit`
        Unit, if any.

    mask : array or `None`
        Mask of the data, if any.

    """
    cols = tab.colnames

    if isinstance(col_idx, int):
        colname = cols[col_idx]
    else:
        colname = col_idx

    coldat = tab[colname]
    data = coldat.data
    unit = coldat.unit

    # Sometimes, Astropy returns masked column.
    if hasattr(data, 'mask'):
        mask = data.mask.flatten()
        data = data.data.flatten()
    else:
        mask = None
        data = data.flatten()

    # If data has no unit, just assume it is the output unit.
    # Otherwise, perform unit conversion.
    if isinstance(to_unit, u.Unit) and to_unit != u.dimensionless_unscaled:
        unit = to_unit
        if unit != u.dimensionless_unscaled and unit != to_unit:
            data = coldat.to(to_unit, equivalencies).value

    return data, unit, mask


class FitsYamlRegister(YamlRegister):
    """
    Defines the generation of `Spectrum1DRef` objects by parsing FITS
    files with information from YAML files.
    """
    def reader(self, filename, **kwargs):
        """This generic function will query the loader factory, which has already
        loaded the YAML configuration files, in an attempt to parse the
        associated FITS file.

        Parameters
        ----------
        filename : str
            Input filename.

        kwargs : dict
            Keywords for Astropy reader.

        """
        logging.info("Attempting to open '{0}' using YAML "
                     "loader '{1}'".format(filename, self._reference.name))

        name = os.path.basename(filename.rstrip(os.sep)).rsplit('.', 1)[0]
        hdulist = fits.open(filename, **kwargs)

        meta = self._reference.meta
        header = dict(hdulist[self._reference.wcs['hdu']].header)
        meta['header'] = header
        wcs = WCS(hdulist[self._reference.wcs['hdu']].header)

        # Usually, all the data should be in this table
        tab = _read_table(hdulist[self._reference.data['hdu']], col_idx=self._reference.data['col'])

        # Read flux column
        data, unit, mask = _read_table_column(tab, self._reference.data['col'])

        # First try to get flux unit from YAML
        if self._reference.data.get('unit') is not None:
            unit = u.Unit(self._reference.data['unit'])
        # Get flux unit from header if there wasn't one in the table column
        elif unit is None:
            unit = _flux_unit_from_header(meta['header'])

        # Get data mask, if not in column.
        # 0/False = good data (unlike Layers)
        if mask is None:
            mask = np.zeros(data.shape, dtype=np.int)
        else:
            mask = mask.astype(np.int)

        # Read in DQ column if it exists
        # 0/False = good (everything else bad)
        if hasattr(self._reference, 'mask') and self._reference.mask.get('hdu') is not None:
            if self._reference.mask['hdu'] == self._reference.data['hdu']:
                dqtab = tab
            else:
                dqtab = _read_table(
                    hdulist[self._reference.mask['hdu']], col_idx=self._reference.mask['col'])

            mask2 = _read_table_column(dqtab, self._reference.mask['col'])[0]  # Data only
            mask |= mask2 # Combine with existing mask

        mask_def = None
        if hasattr(self._reference, 'mask_def') and self._reference.mask_def.get('file') is not None:
            mask_file = self._reference.mask_def.get('file')

            # first check if the mask file is distributed with the packaged
            # then the ~/.specviz, then the current directory
            mod_path = os.path.join(os.path.dirname(__file__), 'yaml_loaders')
            usr_path = os.path.join(os.path.expanduser('~'), '.specviz')
            paths = [mod_path, usr_path, '.']
            for path in paths:
                if os.path.join(path, mask_file):
                    try:
                        logging.info("Trying to load {}".format(os.path.join(path, mask_file)))
                        mask_def = ascii.read(os.path.join(path, mask_file))
                        break
                    except IOError:
                        logging.info("Mask file {} does not exist".format(mask_file))

            if self._reference.mask_def.get('name') is not None:
                mask_def.columns[self._reference.mask_def.get('name')].name = 'NAME'
            if self._reference.mask_def.get('bit') is not None:
                mask_def.columns[self._reference.mask_def.get('bit')].name = 'BIT'
            if self._reference.mask_def.get('description') is not None:
                mask_def.columns[self._reference.mask_def.get('description')].name = 'DESCRIPTION'

            meta['mask_def'] = mask_def

        # Wavelength constructed from WCS by default
        dispersion = None
        disp_unit = None

        # Read in wavelength column if it exists
        if hasattr(self._reference, 'dispersion'):
            if self._reference.dispersion.get('hdu') is not None:
                if self._reference.dispersion['hdu'] == self._reference.data['hdu']:
                    wavtab = tab
                else:
                    wavtab = _read_table(hdulist[self._reference.dispersion['hdu']],
                                         col_idx=self._reference.dispersion['col'])
                dispersion, disp_unit = _read_table_column(
                    wavtab, self._reference.dispersion['col'])[:2]  # Ignore mask

            # Overrides wavelength unit from YAML
            if self._reference.dispersion.get('unit') is not None:
                disp_unit = u.Unit(self._reference.dispersion['unit'])

            # If no unit, try to use WCS
            if disp_unit == u.dimensionless_unscaled:
                disp_unit = None

        # Read flux uncertainty
        if hasattr(self._reference, 'uncertainty') and self._reference.uncertainty.get('hdu') is not None:
            if self._reference.uncertainty['hdu'] == self._reference.data['hdu']:
                errtab = tab
            else:
                errtab = _read_table(
                    hdulist[self._reference.uncertainty['hdu']], col_idx=self._reference.uncertainty['col'])

            uncertainty = _read_table_column(
                errtab, self._reference.uncertainty['col'], to_unit=unit)[0]  # Data only
            uncertainty_type = self._reference.uncertainty.get('type', 'std')
        else:
            uncertainty = np.zeros(data.shape)
            uncertainty_type = 'std'

        # This is dictated by the type of the uncertainty.
        uncertainty = _set_uncertainty(uncertainty, uncertainty_type)

        hdulist.close()

        return Spectrum1DRef(name=name, data=data, unit=unit, uncertainty=uncertainty,
                    mask=mask, wcs=wcs, dispersion=dispersion,
                    dispersion_unit=disp_unit, meta=meta)


class AsciiYamlRegister(YamlRegister):
    """
    Defines the generation of `Spectrum1DRef` objects by parsing ASCII
    files with information from YAML files.
    """
    def reader(self, filename, **kwargs):
        """Like :func:`fits_reader` but for ASCII file."""
        name = os.path.basename(filename.rstrip(os.sep)).rsplit('.', 1)[0]
        tab = ascii.read(filename, **kwargs)
        cols = tab.colnames

        meta = self._reference.meta
        meta['header'] = {}

        # Only loads KEY=VAL comment entries into header
        if 'comments' in tab.meta:
            for s in tab.meta['comments']:
                if '=' not in s:
                    continue
                s2 = s.split('=')
                meta['header'][s2[0]] = s2[1]

        wcs = None
        wave = tab[cols[self._reference.dispersion['col']]]
        dispersion = wave.data
        flux = tab[cols[self._reference.data['col']]]
        data = flux.data
        uncertainty = np.zeros(data.shape)
        uncertainty_type = 'std'

        if flux.unit is None:
            unit = u.Unit(self._reference.data.get('unit', default_fluxunit))
        else:
            unit = flux.unit

        if wave.unit is None:
            disp_unit = u.Unit(self._reference.dispersion.get('unit', default_waveunit))
        else:
            disp_unit = wave.unit

        # Since there's no WCS, include the dispersion unit in the meta data
        meta['header']['cunit'] = [disp_unit.to_string(), unit.to_string()]

        # 0/False = good data (unlike Layers)
        mask = np.zeros(data.shape, dtype=np.bool)

        if hasattr(self._reference, 'uncertainty') and self._reference.uncertainty.get('col') is not None:
            try:
                uncertainty = tab[cols[self._reference.uncertainty['col']]].data
            except IndexError:
                pass  # Input has no uncertainty column
            else:
                uncertainty_type = self._reference.uncertainty.get('type', 'std')

        # This is dictated by the type of the uncertainty.
        uncertainty = _set_uncertainty(uncertainty, uncertainty_type)

        if hasattr(self._reference, 'mask') and self._reference.mask.get('col') is not None:
            try:
                mask = tab[cols[self._reference.mask['col']]].data.astype(np.bool)
            except IndexError:
                pass  # Input has no mask column

        return Spectrum1DRef(name=str(name), data=data, dispersion=dispersion,
                    uncertainty=uncertainty, mask=mask, wcs=wcs,
                    unit=unit, dispersion_unit=disp_unit, meta=meta)



class LineListYamlRegister(YamlRegister):
    """
    Defines the generation of `Spectrum1DRef` objects by parsing LineList
    files with information from YAML files.
    """
    def reader(self, filename, **kwargs):
        names_list = []
        start_list = []
        end_list = []
        units_list = []
        for k in range(len((self._reference.columns))):
            name = self._reference.columns[k][linelist.COLUMN_NAME]
            names_list.append(name)

            start = self._reference.columns[k][linelist.COLUMN_START]
            end = self._reference.columns[k][linelist.COLUMN_END]
            start_list.append(start)
            end_list.append(end)

            if linelist.UNITS_COLUMN in self._reference.columns[k]:
                units = self._reference.columns[k][linelist.UNITS_COLUMN]
            else:
                units = ''
            units_list.append(units)

        tab = ascii.read(filename, format = self._reference.format,
                         names = names_list,
                         col_starts = start_list,
                         col_ends = end_list)

        for k, colname in enumerate(tab.columns):
            tab[colname].unit = units_list[k]

        # The table name (for e.g. display purposes)
        # is taken from the 'name' element in the
        # YAML file descriptor.

        return LineList(tab)
