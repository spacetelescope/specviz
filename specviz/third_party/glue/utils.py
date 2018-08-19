from astropy import units as u
from astropy.wcs import WCSSUB_SPECTRAL

from specutils import Spectrum1D
from glue.core.subset import Subset
from glue.core.coordinates import WCSCoordinates

__all__ = ['is_glue_data_1d_spectrum', 'glue_data_to_spectrum1d']


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
    return (isinstance(data.coords, WCSCoordinates) and
            data.coords.wcs.wcs.spec >= 0)


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

    # Find spectral axis
    spec_axis = data.coords.wcs.naxis - 1 - data.coords.wcs.wcs.spec

    # Find non-spectral axes
    axes = tuple(i for i in range(data.ndim) if i != spec_axis)

    # Collapse values to profile
    values = data.compute_statistic(statistic, attribute, axis=axes, subset_state=subset_state)

    # Get units and attach to value
    component = data.get_component(attribute)

    if component.units is None:
        values = values * u.one
    else:
        values = values * u.Unit(component.units)

    # Get spectral WCS
    wcs_spec = data.coords.wcs.sub([WCSSUB_SPECTRAL])

    return Spectrum1D(values, wcs=wcs_spec)
