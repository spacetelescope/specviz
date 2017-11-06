import logging
from astropy import convolution
from collections import OrderedDict
import numpy as np


def smooth(data, kernel, *args, **kwargs):
    """
    Operates on a spectrum object to return a new, convolved, data set.

    Parameters
    ----------
    data : :class:`~specviz.core.data.Spectrum1DRefLayer`
        The data layer that is being used in the smoothing operation.
    kernel : str
        String representation of the kernel class used for the convolution.
    args : list
        List of args to pass to the kernel object.
    kwargs : dict
        Dict of keyword args to pass to the kernel object.

    Returns
    -------
    new_data : :class:`~specviz.core.data.Spectrum1DRefLayer`
        The new, convolved, data layer.
    """
    kernel = getattr(convolution, kernel)(*args, **kwargs)

    if kernel is None:
        logging.error("Kernel {} is not currently supported.".format(kernel))
        return

    raw_data = convolution.convolve(data.masked_data, kernel)

    new_data = data.__class__(data=raw_data, unit=data.unit,
                              dispersion=data.masked_dispersion,
                              uncertainty=np.zeros(data.uncertainty.array.shape),
                              dispersion_unit=data.dispersion_unit,
                              name="Smoothed {}".format(data.name))

    return new_data
