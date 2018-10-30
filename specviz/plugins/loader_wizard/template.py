import os

from astropy.io import fits
from astropy.wcs import WCS
from astropy.units import Unit
from astropy.nddata import StdDevUncertainty

from specutils.io.registers import data_loader
from specutils import Spectrum1D


def fits_identify(file_name, *args, **kwargs):
    # This function ensures that the file that's trying to be read by this
    # loader is in fact a fits file, or something that can be understood
    # by Astropy's fits loader.
    return (isinstance(file_name, str) and
            args[0].lower().split('.')[-1] in ['fits', 'fit', 'fits.gz'])


@data_loader(label="hlsp-synth", identifier=fits_identify)
def simple_generic_loader(file_name, **kwargs):
    # Get a name to use for the spectra object that's created when the data is loaded.
    # Here, we'll just get the name of the file itself.
    name = os.path.basename(file_name.rstrip(os.sep)).rsplit('.', 1)[0]

    # Now, open the fits file
    with fits.open(file_name, **kwargs) as hdulist:
        # We grab the entire header object. We'll stick this in the spectrum's meta
        # data dictionary so we can always have it inside SpecViz. This is useful
        # when we want to export a spectrum created using this data, for example.
        header = hdulist[0].header
        flux = hdulist[3].data['flux_obs']
        wavelength = hdulist[3].data['disp_obs']

    # Dump the header into the meta dictionary
    meta = {'header': header}
    # print(header)
    # Try and parse the WCS information from the header
    wcs = WCS(header)

    # Here, I set the unit explicitly, but you can imagine passing in a string from
    # the fit file's header instead.
    unit = Unit('erg / (Angstrom cm2 s)')
    disp_unit = Unit('Angstrom')

    # Uncertainties should be explicitly defined. Currently, only standard deviation
    # uncertainties are supported. All this means is that uncertainties will be
    # correctly handled when doing spectrum arithmetic (e.g. propagation, etc). You
    # can get more informatino about this from http://docs.astropy.org/en/stable/nddata/ccddata.html#uncertainty
    # uncertainty = StdDevUncertainty(err)

    # A new spectrum object is returned, which specviz understands
    return Spectrum1D(data=flux,
                      spectral_axis=wavelength,
                      spectral_axis_unit=disp_unit,
                      wcs=wcs, unit=unit, meta=meta)

