import numpy as np

from astropy.modeling import Fittable1DModel, models
from astropy.modeling.parameters import Parameter

__all__ = ['GaussianAbsorption']


class GaussianAbsorption(Fittable1DModel):
    """
    The Gaussian absorption profile.

    This is defined in terms of the emission Gaussian1D model.

    """
    amplitude = Parameter(default=1., min=0.)
    mean = Parameter(default=1.)
    stddev = Parameter(default=1.)

    @staticmethod
    def evaluate(x, amplitude, mean, stddev):
        """
        GaussianAbsorption model function.
        """
        return models.Gaussian1D.evaluate(x, -amplitude, mean, stddev)

    @staticmethod
    def fit_deriv(x, amplitude, mean, stddev):
        """
        GaussianAbsorption model function derivatives.
        """
        import operator
        return list(map(operator.neg, models.Gaussian1D.fit_deriv(x, -amplitude, mean, stddev)))


class GaussianAbsorptionInitializer(object):
    """
    `GaussianAbsorption` model initializer
    """

    def initialize(self, instance, wave, flux):
        """
        Initialize the absorption Gaussian model

        Parameters
        ----------
        instance: GaussianAbsorption
            The `GaussianAbsorption` model

        wave: numpy.ndarray
            The wavelength range.

        flux: numpy.ndarray
            The source flux to normalize to.
        """
        instance.wave = wave
        instance.flux = flux

        # start by computing an approximate linear continuum
        s, i = self._initialize_linear(wave, flux)
        continuum = models.Linear1D(slope=s, intercept=i)(wave)

        # centroid is computed by subtracting this continuum
        # estimate and then using it in the same way that is
        # used for computing the centroid of the emission Gaussian.
        flux_s = flux - continuum
        centroid = np.sum(wave * flux_s) / np.sum(flux_s)

        # sigma is computed in the same way as with the emission
        # Gaussian, but again using the continuum-subtracted data.
        dw = wave - np.mean(wave)
        fwhm = 2 * np.sqrt(np.sum((dw * dw) * flux_s) / np.sum(flux_s))
        sigma = fwhm / 2.355

        # amplitude is estimated from the difference in areas under the
        # (interpolated) linear continuum and the actual data.
        delta_w = wave[1:] - wave[:-1]
        sum_c = np.sum(continuum[1:] * delta_w)
        sum_f = np.sum(flux[1:] * delta_w)
        amplitude = (sum_c - sum_f) / (sigma * np.sqrt( 2 * np.pi))

        instance.amplitude = amplitude.value
        instance.mean = centroid.value
        instance.stddev = sigma.value

    def _initialize_linear(self, w, f):

        # compute averages at the 5% of data at each extreme of the wavelength range.
        l = int(len(w) / 20)
        w1 = np.mean(w[0:l])
        w2 = np.mean(w[-l-1:-1])
        f1 = np.mean(f[0:l])
        f2 = np.mean(f[-l-1:-1])

        # fit a straigth line thru these
        slope = (f2 - f1) / (w2 - w1)
        inter = f2 - slope * w2

        return slope, inter
