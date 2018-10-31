import pytest
import numpy as np
from numpy.testing import assert_allclose

from astropy import units as u
from astropy.wcs import WCS
from astropy.tests.helper import assert_quantity_allclose

pytest.importorskip("glue")  # noqa

from glue.core import Data
from glue.core.component import Component
from glue.core.coordinates import WCSCoordinates

from ..utils import glue_data_has_spectral_axis, glue_data_to_spectrum1d, SpectralCoordinates


def test_conversion_utils_notspec():
    data = Data(label='not spectrum')
    assert not glue_data_has_spectral_axis(data)


def test_conversion_utils_1d():

    # Set up simple spectral WCS
    wcs = WCS(naxis=1)
    wcs.wcs.ctype = ['VELO-LSR']
    wcs.wcs.set()

    # Set up glue Coordinates object
    coords = WCSCoordinates(wcs=wcs)

    data = Data(label='spectrum', coords=coords)
    data.add_component(Component(np.array([3.4, 2.3, -1.1, 0.3]), units='Jy'), 'x')

    assert glue_data_has_spectral_axis(data)

    spec = glue_data_to_spectrum1d(data, data.id['x'])
    assert_quantity_allclose(spec.spectral_axis, [1, 2, 3, 4] * u.m / u.s)
    assert_quantity_allclose(spec.flux, [3.4, 2.3, -1.1, 0.3] * u.Jy)


def test_conversion_utils_3d():

    # Set up simple spectral WCS
    wcs = WCS(naxis=3)
    wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN', 'VELO-LSR']
    wcs.wcs.set()

    # Set up glue Coordinates object
    coords = WCSCoordinates(wcs=wcs)

    data = Data(label='spectral-cube', coords=coords)
    data.add_component(Component(np.ones((3, 4, 5)), units='Jy'), 'x')

    assert glue_data_has_spectral_axis(data)

    spec = glue_data_to_spectrum1d(data, data.id['x'], statistic='sum')
    assert_quantity_allclose(spec.spectral_axis, [1, 2, 3] * u.m / u.s)
    assert_quantity_allclose(spec.flux, [20, 20, 20] * u.Jy)


def test_conversion_utils_spectral_coordinates():

    # Set up glue Coordinates object
    coords = SpectralCoordinates([1, 4, 10] * u.micron)

    data = Data(label='spectrum1d', coords=coords)
    data.add_component(Component(np.array([3, 4, 5]), units='Jy'), 'x')

    assert_allclose(data.coords.pixel2world([0, 0.5, 1, 1.5, 2]),
                    [[1, 2.5, 4, 7, 10]])

    assert glue_data_has_spectral_axis(data)

    spec = glue_data_to_spectrum1d(data, data.id['x'])
    assert_quantity_allclose(spec.spectral_axis, [1, 4, 10] * u.micron)
    assert_quantity_allclose(spec.flux, [3, 4, 5] * u.Jy)
