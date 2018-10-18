import os

from astropy.io import fits
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty

from specutils.io.registers import data_loader
from specutils import Spectrum1D

__all__ = ['stis_identify', 'stis_spectrum_loader']


def stis_identify(*args, **kwargs):
    """
    Check whether given file contains HST/STIS spectral data.
    """

    with fits.open(args[0]) as hdu:
        if hdu[0].header['TELESCOP'] == 'HST' and hdu[0].header['INSTRUME'] == 'STIS':
           return True

    return False


@data_loader(label="HST/STIS",identifier=stis_identify)
def stis_spectrum_loader(file_name, **kwargs):
    """ Load file from STIS spectral data into a spectrum object

    Parameters
    ----------
    file_name: str
        The path to the FITS file

    Returns
    -------
    data: Spectrum1D
        The data.
    """

    name = os.path.basename(file_name)

    with fits.open(file_name, **kwargs) as hdu:
        header = hdu[0].header
        meta = {'header': header}

        unit = Unit("erg/cm**2 Angstrom s")
        disp_unit = Unit('Angstrom')
        dispersion = hdu[1].data['wavelength'].flatten() * disp_unit
        data = hdu[1].data['FLUX'].flatten() * unit
        uncertainty = StdDevUncertainty(hdu[1].data["ERROR"].flatten() * unit)

    return Spectrum1D(flux=data * unit,
                      spectral_axis=dispersion,
                      uncertainty=uncertainty,
                      meta=meta)
