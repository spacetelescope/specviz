"""
Loader for SDSS individual spectrum files: spec_ files.

.. _spec: https://data.sdss.org/datamodel/files/BOSS_SPECTRO_REDUX/RUN2D/spectra/PLATE4/spec.html
"""
import os
import re

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.units import Unit, def_unit
from astropy.nddata import StdDevUncertainty

import numpy as np

from ...interfaces import data_loader
from ...core.data import Spectrum1DRef

__all__ = ['spec_identify', 'spSpec_identify',
           'spec_loader', 'spSpec_loader']

_spSpec_pattern = re.compile(r'spSpec-\d{5}-\d{4}-\d{3}\.fit')
_spec_pattern = re.compile(r'spec-\d{4,5}-\d{5}-\d{4}\.fits')


def spec_identify(*args, **kwargs):
    """
    Check whether given filename is FITS. This is used for Astropy I/O
    Registry.
    """
    return (isinstance(args[0], str) and
            _spec_pattern.match(args[0]) is not None)


def spSpec_identify(*args, **kwargs):
    """
    Check whether given filename is FITS. This is used for Astropy I/O
    Registry.
    """
    return (isinstance(args[0], str) and
            _spSpec_pattern.match(args[0]) is not None)


@data_loader(label="SDSS-III/IV spec", identifier=spec_identify)
def spec_loader(file_name, **kwargs):
    """
    Loader for SDSS-III/IV spec files.

    Parameters
    ----------
    file_name: str
        The path to the FITS file

    Returns
    -------
    data: Spectrum1DRef
        The data.
    """
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]
    hdulist = fits.open(file_name, **kwargs)

    header = hdulist[0].header
    meta = {'header': header}

    # spectrum is in HDU 1
    data = hdulist[1].data['flux']
    unit = Unit('1e-17 erg / (Angstrom cm2 s)')

    # Because there is no object that explicitly supports inverse variance.
    stdev = np.sqrt(1.0/hdulist[1].data['ivar'])
    uncertainty = StdDevUncertainty(stdev)

    dispersion = 10**hdulist[1].data['loglam']
    dispersion_unit = Unit('Angstrom')

    mask = hdulist[1].data['and_mask'] != 0
    hdulist.close()

    return Spectrum1DRef(name=name, data=data, unit=unit, uncertainty=uncertainty,
                         dispersion=dispersion, dispersion_unit=dispersion_unit,
                         mask=mask, meta=meta)


@data_loader(label="SDSS-I/II spSpec", identifier=spSpec_identify)
def spSpec_loader(file_name, **kwargs):
    """
    Loader for SDSS-I/II spSpec files.

    Parameters
    ----------
    file_name: str
        The path to the FITS file

    Returns
    -------
    data: Spectrum1DRef
        The data.
    """
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]
    hdulist = fits.open(file_name, **kwargs)

    header = hdulist[0].header
    meta = {'header': header}
    wcs = WCS(hdulist[0].header)

    data = hdulist[0].data[0, :]
    unit = Unit('1e-17 erg / (Angstrom cm2 s)')

    uncertainty = StdDevUncertainty(hdulist[0].data[2, :])

    # dispersion from the WCS but convert out of logspace
    # dispersion = 10**wcs.all_pix2world(np.arange(data.shape[0]), 0)[0]
    dispersion = 10**wcs.all_pix2world(np.vstack((np.arange(data.shape[0]),
                                                  np.zeros((data.shape[0],)))).T,
                                       0)[:, 0]
    # dispersion = 10**hdulist[1].data['loglam']
    dispersion_unit = Unit('Angstrom')

    mask = hdulist[0].data[3, :] != 0
    hdulist.close()

    return Spectrum1DRef(name=name, data=data, unit=unit, uncertainty=uncertainty,
                         dispersion=dispersion, dispersion_unit=dispersion_unit,
                         mask=mask, meta=meta)
