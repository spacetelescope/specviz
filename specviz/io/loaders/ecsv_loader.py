import os

from astropy.table import Table

from ...interfaces import data_loader
from ...core.data import Spectrum1DRef

__all__ = ['ecsv_identify', 'ecsv_spectrum_loader']


def ecsv_identify(*args, **kwargs):
    """ Check if it's an ECSV file.

    """
    name = os.path.basename(args[0])

    if name.lower().split('.')[-1] == 'ecsv':
       return True

    return False


@data_loader(label="Spectrum ECSV", priority=10, identifier=ecsv_identify,
             extensions=["ecsv", "ECSV"])
def ecsv_spectrum_loader(file_name, **kwargs):
    """ Load spectrum from ECSV file

    Parameters
    ----------
    file_name: str
        The path to the ECSV file

    Returns
    -------
    data: Spectrum1DRef
        The data.
    """

    table = Table.read(file_name, format='ascii.ecsv')

    return Spectrum1DRef.from_array(data=table['Intensity'],
                                    dispersion=table['Wavelength'],
                                    unit=table['Intensity'].unit,
                                    dispersion_unit=table['Wavelength'].unit,
                                    meta=table.meta)
