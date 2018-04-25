"""
Generic loader definitions
"""
import os

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty

from ...interfaces.decorators import data_loader, data_writer
from ...core.data import Spectrum1DRef

__all__ = ['fits_identify', 'simple_generic_loader', 'simple_generic_writer']


def fits_identify(*args, **kwargs):
    """
    Check whether given filename is FITS. This is used for Astropy I/O
    Registry.
    """
    return (isinstance(args[0], str) and
            args[0].lower().split('.')[-1] in ['fits', 'fit', 'fits.gz'])



def simple_generic_writer(data, file_name, **kwargs):
    """
    Basic `Spectrum1DRef` FITS writer.
    """
    # Create fits columns
    flux_col = fits.Column(name='FLUX', format='E', array=data.data)
    disp_col = fits.Column(name='WAVE', format='E', array=data.dispersion)
    uncert_col = fits.Column(name='UNCERT', format='E', array=data.uncertainty.array)
    mask_col = fits.Column(name='MASK', format='L', array=data.mask)

    cols = fits.ColDefs([flux_col, disp_col, uncert_col, mask_col])

    # Create the bin table
    tbhdu = fits.BinTableHDU.from_columns(cols)

    # Create header
    prihdu = fits.PrimaryHDU(header=data.meta.get('header', data.wcs.to_header() if data.wcs is not None else None))

    # Compose
    thdulist = fits.HDUList([prihdu, tbhdu])
    thdulist.writeto("{}.fits".format(file_name), overwrite=True)


@data_loader(label="Simple Fits", identifier=fits_identify, extensions=["fits", "fit"],
             writer=simple_generic_writer)
def simple_generic_loader(file_name, **kwargs):
    """
    Basic FITS file loader

    Presumption is the primary data is a table with columns 'flux'
    and 'err'.  The dispersion information is encoded in the FITS
    header keywords.

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
    wcs = WCS(hdulist[0].header)
    unit = Unit('Jy')
    uncertainty = StdDevUncertainty(tab["err"])
    data = tab["flux"]

    hdulist.close()

    return Spectrum1DRef(data=data, name=name, wcs=wcs,
                         uncertainty=uncertainty, unit=unit, meta=meta)
