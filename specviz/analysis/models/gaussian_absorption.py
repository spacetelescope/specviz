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

