import os

from astropy.io import fits
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty

from specutils.io.registers import data_loader
from specutils import Spectrum1D

__all__ = ['cos_identify', 'cos_spectrum_loader']


def cos_identify(*args, **kwargs):
    """Check whether given file contains HST/COS spectral data."""
    with fits.open(args[0]) as hdu:
        if hdu[0].header['TELESCOP'] == 'HST' and hdu[0].header['INSTRUME'] == 'COS':
           return True

    return False


@data_loader(label="HST/COS", identifier=cos_identify)
def cos_spectrum_loader(file_name, **kwargs):
    """
    Load file from COS spectral data into a spectrum object.

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

        data = hdu[1].data['FLUX'].flatten()
        dispersion = hdu[1].data['wavelength'].flatten() * Unit('Angstrom')
        unit = Unit("erg/cm**2 Angstrom s")
        uncertainty = StdDevUncertainty(hdu[1].data["ERROR"].flatten() * unit)

    return Spectrum1D(flux=data * unit,
                      spectral_axis=dispersion,
                      uncertainty=uncertainty,
                      unit=unit,
                      meta=meta)
