"""
Loader for aspcapStar_ files.

.. _aspcapStar: https://data.sdss.org/datamodel/files/APOGEE_REDUX/APRED_VERS/APSTAR_VERS/ASPCAP_VERS/RESULTS_VERS/LOCATION_ID/aspcapStar.html

TODO
----

* Add support for apVisit, apStar files.

"""
import os

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.units import Unit, def_unit
from astropy.nddata import StdDevUncertainty

import numpy as np

from specviz.interfaces import data_loader
from specviz.core.data import Spectrum1DRef

__all__ = ['aspcapStar_identify', 'aspcapStar_loader']


def aspcapStar_identify(*args, **kwargs):
    """
    Check whether given filename is FITS. This is used for Astropy I/O
    Registry.
    """
    return (isinstance(args[0], str) and
            args[0].lower().split('.')[-1] == 'fits' and
            args[0].startswith('aspcapStar'))


@data_loader(label="APOGEE aspcapStar", identifier=aspcapStar_identify)
def aspcapStar_loader(file_name, **kwargs):
    """
    Loader for APOGEE aspcapStar files.

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

    tab = Table.read(file_name)

    meta = {'header': header}
    wcs = WCS(hdulist[1].header)

    data = hdulist[1].data # spectrum in the first extension
    unit = def_unit('arbitrary units')
    # unit = Unit('Jy') / Unit('Jy')  # make the flux unitless

    uncertainty = StdDevUncertainty(hdulist[2].data)

    # dispersion from the WCS but convert out of logspace
    dispersion = 10**wcs.all_pix2world(np.arange(data.shape[0]), 0)[0]
    dispersion_unit = Unit('Angstrom')
    hdulist.close()

    return Spectrum1DRef(name=name, data=data, unit=unit, uncertainty=uncertainty,
                         dispersion=dispersion, dispersion_unit=dispersion_unit,
                         meta=meta)
