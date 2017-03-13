"""
Generic loader definitions
"""
import os

from astropy.io import fits
from astropy.table import Table
from astropy.wcs import WCS
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty

from ...interfaces import data_writer
from ...core.data import Spectrum1DRef

__all__ = ['fits_identify', 'simple_generic_loader']


@data_writer(label="Simple Fits")
def simple_generic_loader(data, file_name, **kwargs):
    """
    Basic `Spectrum1DRef` FITS writer.
    """
    # Create fits columns
    flux_col = fits.Column(name='FLUX', format='E', array=data.unmasked_data.value)
    disp_col = fits.Column(name='FLUX', format='E', array=data.unmasked_dispersion.value)
    uncert_col = fits.Column(name='FLUX', format='E', array=data.unmasked_raw_uncertainty.data)
    mask_col = fits.Column(name='FLUX', format='E', array=data.dispersion)
    cols = fits.ColDefs([col1, col2])

    # Create the bin table
    tbhdu = fits.BinTableHDU.from_columns(cols)

    # Create header
    prihdr = fits.Header()
    prihdr['OBSERVER'] = 'Edwin Hubble'
    prihdr['COMMENT'] = "Here's some commentary about this FITS file."
    prihdu = fits.PrimaryHDU(header=prihdr)

    # Compose
    thdulist = fits.HDUList([prihdu, tbhdu])
    thdulist.writeto(file_name)
