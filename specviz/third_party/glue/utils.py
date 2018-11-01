import numpy as np

from astropy import units as u
from astropy.wcs import WCSSUB_SPECTRAL

from specutils import Spectrum1D
from glue.core.subset import Subset
from glue.core.coordinates import Coordinates, WCSCoordinates

__all__ = ['glue_data_has_spectral_axis', 'glue_data_to_spectrum1d']


class SpectralCoordinates(Coordinates):
    """
    This is a sub-class of Coordinates that is intended for 1-d spectral axes
    given by a :class:`~astropy.units.Quantity` array.
    """

    def __init__(self, values):
        self._index = np.arange(len(values))
        self._values = values

    @property
    def spectral_axis(self):
        return self._values

    def world2pixel(self, *world):
        return tuple(np.interp(world, self._values.value, self._index,
                               left=np.nan, right=np.nan))

    def pixel2world(self, *pixel):
        return tuple(np.interp(pixel, self._index, self._values.value,
                               left=np.nan, right=np.nan))

    def dependent_axes(self, axis):
        return (axis,)


def glue_data_has_spectral_axis(data):
    """
    Check whether a glue Data object is a 1D spectrum.

    Parameters
    ----------
    data : `glue.core.data.Data`
        The data to check
    """

    if isinstance(data, Subset):
        data = data.data

    if isinstance(data.coords, SpectralCoordinates):
        return True

    if not isinstance(data.coords, WCSCoordinates):
        return False

    spec_axis = data.coords.wcs.naxis - 1 - data.coords.wcs.wcs.spec

    return (isinstance(data.coords, WCSCoordinates) and
            spec_axis >= 0)


def glue_data_to_spectrum1d(data_or_subset, attribute, statistic='mean'):
    """
    Convert a glue Data object to a Spectrum1D object.

    Parameters
    ----------
    data_or_subset : `glue.core.data.Data` or `glue.core.subset.Subset`
        The data to convert to a Spectrum1D object
    attribute : `glue.core.component_id.ComponentID`
        The attribute to use for the Spectrum1D data
    statistic : {'minimum', 'maximum', 'mean', 'median', 'sum', 'percentile'}
        The statistic to use to collapse the dataset
    """

    if isinstance(data_or_subset, Subset):
        data = data_or_subset.data
        subset_state = data_or_subset.subset_state
    else:
        data = data_or_subset
        subset_state = None

    if isinstance(data.coords, WCSCoordinates):

        # Find spectral axis
        spec_axis = data.coords.wcs.naxis - 1 - data.coords.wcs.wcs.spec

        # Find non-spectral axes
        axes = tuple(i for i in range(data.ndim) if i != spec_axis)

        kwargs = {'wcs': data.coords.wcs.sub([WCSSUB_SPECTRAL])}

    elif isinstance(data.coords, SpectralCoordinates):

        kwargs = {'spectral_axis': data.coords.spectral_axis}

    else:

        raise TypeError('data.coords should be an instance of WCSCoordinates or SpectralCoordinates')

    component = data.get_component(attribute)

    # Collapse values to profile
    if data.ndim > 1:
        # Get units and attach to value
        values = data.compute_statistic(statistic, attribute, axis=axes,
                                        subset_state=subset_state)
    else:
        values = component.data

    if component.units is None:
        values = values * u.one
    else:
        values = values * u.Unit(component.units)

    return Spectrum1D(values, **kwargs)
