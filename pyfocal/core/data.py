"""This module handles spectrum data objects."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import logging

# THIRD-PARTY
import numpy as np
from astropy.nddata import NDData, NDArithmeticMixin, NDIOMixin
from astropy.units import Unit, Quantity


class Data(NDIOMixin, NDArithmeticMixin, NDData):
    """Class of the base data container for all data (of type
    :class:`numpy.ndarray`) that is passed around in Pyfocal. It inherits from
    :class:`astropy.nddata.NDData` and provides functionality for arithmetic
    operations, I/O, and slicing.

    Parameters
    ----------
    data : ndarray
        Flux values.

    dispersion : ndarray or `None`
        Dispersion values. If not given, this is calculated from WCS.

    dispersion_unit : `~astropy.units.Unit` or `None`
        Dispersion unit. If not given, this is obtained from WCS.

    name : str
        Short description of the spectrum.

    args : tuple
        Additional positional arguments.

    kwargs : dict
        Additional keyword arguments.

    Examples
    --------
    >>> d = Data.read(
    ...     'generic_spectra.fits', filter='Generic Fits (*.fits *.mits)')
    >>> d = Data.read(
    ...     'generic_spectra.txt', filter='ASCII (*.txt *.dat)')

    """
    def __init__(self, data, dispersion=None, dispersion_unit=None, name="",
                 *args, **kwargs):
        super(Data, self).__init__(data, *args, **kwargs)
        self._dispersion = dispersion
        self._dispersion_unit = dispersion_unit
        self.name = name or "New Data Object"
        self._layers = []

    # NOTE: Cannot have docstring here or Astropy will throw error!
    @classmethod
    def read(cls, *args, **kwargs):
        from ..interfaces.registries import io_registry

        return io_registry.read(cls, *args, **kwargs)

    @property
    def dispersion(self):
        """Dispersion values."""
        if self._dispersion is None:
            self._dispersion = np.arange(self.data.size)

            try:
                crval = self.wcs.wcs.crval[0]
                cdelt = self.wcs.wcs.cdelt[0]
                end = self.data.shape[0] * cdelt + crval
                self._dispersion = np.arange(crval, end, cdelt)
            except:
                logging.warning("Invalid FITS headers; constructing default "
                                "dispersion array.")

        return self._dispersion

    @property
    def dispersion_unit(self):
        """Unit of dispersion."""
        if self._dispersion_unit is None:
            try:
                self._dispersion_unit = self.wcs.wcs.cunit[0]
            except AttributeError:
                logging.warning("No dispersion unit information in WCS.")
                self._dispersion_unit = Unit("")

        return self._dispersion_unit


class Layer(object):
    """Class to handle layers in Pyfocal.

    A layer is a "view" into a :class:`Data` object. It does
    not hold any data itself, but instead contains a special ``mask`` object
    and reference to the original data.

    Since :class:`Data` inherits from
    :class:`astropy.nddata.NDDataBase` and provides the
    :class:`astropy.nddata.NDArithmeticMixin` mixin, it is also possible to
    do arithmetic operations on layers.

    Parameters
    ----------
    source : `Data`
        Spectrum data object.
    mask : ndarray
        Mask for the spectrum data.
    parent : obj or `None`
        GUI parent.
    window : obj or `None`
        GUI window.
    name : str
        Short description.
    """
    def __init__(self, source, mask, parent=None, window=None, name=''):
        super(Layer, self).__init__()
        self._source = source
        self._mask = mask
        self._parent = parent
        self._window = window
        self.name = self._source.name + " Layer" if not name else name
        self.units = (self._source.dispersion_unit,
                      self._source.unit if self._source.unit is not None else "")

    @property
    def data(self):
        """Flux quantity with mask applied."""
        data = self._source.data[self._mask]

        return Quantity(data, unit=self._source.unit).to(self.units[1])

    @property
    def unit(self):
        """Flux unit."""
        return self._source.unit

    @property
    def dispersion(self):
        """Dispersion quantity with mask applied."""
        return Quantity(self._source.dispersion[self._mask],
                        unit=self._source.dispersion_unit).to(self.units[0])

    @dispersion.setter
    def dispersion(self, value, unit=""):
        self._source._dispersion = value

    @property
    def uncertainty(self):
        """Flux uncertainty with mask applied."""
        return self._source.uncertainty[self._mask]

    @property
    def mask(self):
        """Mask for spectrum data."""
        return self._source.mask[self._mask]

    @property
    def wcs(self):
        """WCS for spectrum data."""
        return self._source.wcs

    @property
    def meta(self):
        """Spectrum metadata."""
        return self._source.meta


class ModelLayer(Layer):
    """A layer for spectrum with a model applied.

    Parameters
    ----------
    model : obj
        Astropy model.
    source : `Data`
        Spectrum data object.
    mask : ndarray
        Mask for the spectrum data.
    parent : obj or `None`
        GUI parent.
    window : obj or `None`
        GUI window.
    name : str
        Short description.
    """
    def __init__(self, model, source, mask, parent=None, window=None, name=''):
        name = source.name + " Model Layer" if not name else name
        super(ModelLayer, self).__init__(source, mask, parent, window, name)

        self._data = None
        self._model = model

        logging.info('Created ModelLayer object: {0}'.format(name))

    @property
    def data(self):
        """Flux quantity from model."""
        if self._data is None:
            self._data = self._model(self.dispersion.value)

        return Quantity(self._data,
                        unit=self._source.unit).to(self.units[1])

    @property
    def uncertainty(self):
        """Models do not need to contain uncertainties; override parent
        class method.
        """
        return None

    @property
    def model(self):
        """Spectrum model."""
        return self._model

    @model.setter
    def model(self, value):
        self._model = value
        self._data = self._model(self.dispersion.value)
