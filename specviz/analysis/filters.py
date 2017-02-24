import logging
from astropy import convolution


smoothing_kernels = {
    'gaussian': convolution.Gaussian1DKernel,
    'box': convolution.Box1DKernel,
    'trapezoid': convolution.Trapezoid1DKernel,
    'mexican_hat': convolution.MexicanHat1DKernel
}


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
    if kernel not in smoothing_kernels.keys():
        logging.error("Kernel {} is not currently supported.".format(kernel))
        return

    kernel = smoothing_kernels.get(kernel)(*args, **kwargs)

    raw_data = convolution.convolve(data.data, kernel)

    new_data = data.__class__.copy(data, data=raw_data)

    return new_data
