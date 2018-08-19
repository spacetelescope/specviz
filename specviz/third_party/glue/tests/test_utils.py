import numpy as np

from astropy import units as u
from astropy.wcs import WCS
from astropy.tests.helper import assert_quantity_allclose

from glue.core import Data
from glue.core.component import Component
from glue.core.coordinates import WCSCoordinates

from ..utils import is_glue_data_1d_spectrum, glue_data_to_spectrum1d


def test_conversion_utils():

    # Set up simple spectral WCS
    wcs = WCS(naxis=1)
    wcs.wcs.ctype = ['VELO-LSR']
    wcs.wcs.set()

    # Set up glue Coordinates object
    coords = WCSCoordinates(wcs=wcs)

    data1 = Data(label='spectrum', coords=coords)
    data1.add_component(Component(np.array([3.4, 2.3, -1.1, 0.3]), units='Jy'), 'x')

    data2 = Data(label='not spectrum')

    assert is_glue_data_1d_spectrum(data1)
    assert not is_glue_data_1d_spectrum(data2)

    spec = glue_data_to_spectrum1d(data1, data1.id['x'])
    assert_quantity_allclose(spec.spectral_axis, [1, 2, 3, 4] * u.m / u.s)
    assert_quantity_allclose(spec.flux, [3.4, 2.3, -1.1, 0.3] * u.Jy)
