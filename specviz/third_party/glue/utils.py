from astropy import units as u
from specutils import Spectrum1D
from glue.core.coordinates import WCSCoordinates

__all__ = ['is_glue_data_1d_spectrum', 'glue_data_to_spectrum1d']


def is_glue_data_1d_spectrum(data):
    """
    Check whether a glue Data object is a 1D spectrum.

    Parameters
    ----------
    data : `glue.core.data.Data`
        The data to check
    """
    return (isinstance(data.coords, WCSCoordinates) and
            data.ndim == 1 and
            data.coords.wcs.wcs.spec == 0)


def glue_data_to_spectrum1d(data, attribute):
    """
    Convert a glue Data object to a Spectrum1D object.

    Parameters
    ----------
    data : `glue.core.data.Data`
        The data to convert to a Spectrum1D object
    attribute : `glue.core.component_id.ComponentID`
        The attribute to use for the Spectrum1D data
    """
    component = data.get_component(attribute)
    values = component.data * u.Unit(component.units)
    return Spectrum1D(values, wcs=data.coords.wcs)
