"""
Data Objects
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import re

import numpy as np
from astropy.units import Quantity, LogQuantity, LogUnit, spectral_density, spectral, Unit
from py_expression_eval import Parser

# FIXME: the latest developer version of Astropy removes OrderedDict which is needed by
# the current release of specutils, so we hackily add OrderedDict back to astropy to
# make sure importing specutils does not crash.
from collections import OrderedDict
from astropy import utils
utils.OrderedDict = OrderedDict

from specutils.core.generic import Spectrum1DRef
from astropy.nddata import StdDevUncertainty, UnknownUncertainty

logging.basicConfig(level=logging.INFO)

__all__ = [
    'Spectrum1DRefLayer',
    'Spectrum1DRefModelLayer',
]

def _make_quantity(data, unit):
    """
    Get a LogQuantity if the a LogUnit is used rather than a regular Quantity.

    Parameters
    ----------
    data: numpy.ndarray
        the data
    unit: ~astropy.unit.Unit or ~astropy.unit.LogUnit
        The data units

    Returns
    -------
    ~astropy.unit.Quantity or ~astropy.unit.LogQuantity
        depending on the unit type
    """
    if isinstance(unit, LogUnit):
        return LogQuantity(data, unit=unit)
    else:
        return Quantity(data, unit=unit)


class Spectrum1DRefLayer(Spectrum1DRef):
    """
    Class to handle layers in SpecViz.

    Parameters
    ----------
    data: numpy.ndarray
        The flux.

    wcs: `~astropy.wcs.WCS`
        If specified, the WCS relating pixel to wavelength.

    parent: layer
        If specified, the parent layer.

    layer_mask: layer
        The layer defining the valid data mask.

    args, kwargs:
        Arguments passed to the
        `~spectutils.core.generic.Spectrum1DRef` object.
    """
    def __init__(self, data, wcs=None, parent=None, layer_mask=None,
                 uncertainty=None, unit=None, mask=None, *args,**kwargs):
        # if not issubclass(data.__class__, Spectrum1DRefLayer):
        if uncertainty is None:
            uncertainty = StdDevUncertainty(np.zeros(data.shape))
        elif isinstance(uncertainty, UnknownUncertainty):
            uncertainty = StdDevUncertainty(uncertainty.array)

        if mask is None:
            mask = np.zeros(data.shape).astype(bool)

        super(Spectrum1DRefLayer, self).__init__(data, wcs=wcs, unit=unit,
                                                 uncertainty=uncertainty,
                                                 mask=mask,
                                                 *args,**kwargs)
        self._parent = parent
        self._layer_mask = layer_mask

    @classmethod
    def from_parent(cls, parent, layer_mask=None, name=None, copy=True):
        """
        Create a duplicate child layer from a parent layer

        Parameters
        ----------
        parent: layer
            The layer to duplicate.

        layer_mask: layer
            The layer defining the valid data mask.

        name: str
            Layer's name. If `None`, a name based on the parent
            layer is used.

        Returns
        -------
        child_layer:
            The new layer.
        """
        return cls(name=name or parent.name + " Layer", data=parent.data,
                   unit=parent.unit, uncertainty=parent.uncertainty,
                   mask=parent.mask, wcs=parent.wcs,
                   dispersion=parent.dispersion,
                   dispersion_unit=parent.dispersion_unit,
                   layer_mask=layer_mask, parent=parent, meta=parent.meta,
                   copy=copy)

    def from_self(self, name="", layer_mask=None):
        """
        Create a new, parentless, layer based on this layer

        Parameters
        ----------
        name: str
            Name of the new layer

        layer_mask: layer
            The layer defining the valid data mask.

        Returns
        -------
        new_layer:
            The new, parentless, layer.
        """
        return self.from_parent(
            parent=self._parent, layer_mask=layer_mask, name=name, copy=True
        )

    @classmethod
    def from_formula(cls, formula, layers):
        """
        Create a layer from an operation performed on other layers

        Parameters
        ----------
        formula: str
            The operation to perform on the given layers.

        layers: [layer, ...]
            The layers which are arguments to the given formula.

        Returns
        -------
        new_layer:
            Result of the operation
        """
        if not formula:
            return

        new_layer = cls._evaluate(layers, formula)

        if new_layer is None:
            logging.error(
                "Failed to create new layer from formula: {}".format(formula))
            return

        new_layer.name = "Resultant"

        return new_layer

    @property
    def masked_data(self):
        """Flux quantity with mask applied. Returns a masked array
        containing a Quantity object."""
        data = np.ma.array(
            _make_quantity(self._data, unit=self.unit),
            mask=self.full_mask)

        return data

    @property
    def shape(self):
        return self._data.shape

    @property
    def unit(self):
        return self._unit or Unit("")

    @property
    def masked_dispersion(self):
        """Dispersion quantity with mask applied. Returns a masked array
        containing a Quantity object."""
        self._dispersion = super(Spectrum1DRefLayer, self).dispersion

        dispersion = np.ma.array(
            _make_quantity(self._dispersion, unit=self.dispersion_unit),
            mask=self.full_mask)

        return dispersion

    @property
    def raw_uncertainty(self):
        """Flux uncertainty with mask applied. Returns a masked array
        containing a Quantity object."""
        uncertainty = np.ma.array(
            _make_quantity(self._uncertainty.array, unit=self.unit),
            mask=self.full_mask)

        return uncertainty

    @property
    def unmasked_data(self):
        """Flux quantity with no layer mask applied."""
        data = np.ma.array(
            _make_quantity(self._data, unit=self.unit),
            mask=self.mask)

        return data

    @property
    def unmasked_dispersion(self):
        """Dispersion quantity with no layer mask applied."""
        self._dispersion = super(Spectrum1DRefLayer, self).dispersion

        dispersion = np.ma.array(
            _make_quantity(self._dispersion, unit=self.dispersion_unit),
            mask=self.mask)

        return dispersion

    @property
    def unmasked_raw_uncertainty(self):
        """Flux uncertainty with mask applied. Returns a masked array
        containing a Quantity object."""
        uncertainty = np.ma.array(
            _make_quantity(self._uncertainty.array, unit=self.unit),
            mask=self.mask)

        return uncertainty

    @property
    def layer_mask(self):
        """Mask applied from an ROI."""
        if self._layer_mask is None:
            self._layer_mask = np.ones(self._data.shape).astype(bool)

        return self._layer_mask

    @property
    def full_mask(self):
        """Mask for spectrum data."""
        if self.mask is None or self.layer_mask is None:
            return np.zeros(self._data.shape)

        return self.mask.astype(bool) | ~self.layer_mask.astype(bool)

    def set_units(self, disp_unit=None, data_unit=None):
        """
        Set the dispersion and flux units

        Parameters
        ----------
        disp_unit: `~astropy.units`
            The dispersion units.

        data_unit: `~astropy.units`
            The flux units.
        """
        if disp_unit is not None:
            if (self.dispersion_unit.is_unity() or
                self.dispersion_unit.is_equivalent(disp_unit,
                                                   equivalencies=spectral())):

                if self.dispersion_unit.is_unity():
                    self.dispersion_unit = disp_unit

                self._dispersion = self.masked_dispersion.data.to(
                    disp_unit, equivalencies=spectral()).value

                # Finally, change the unit
                self.dispersion_unit = disp_unit
            else:
                logging.warning("Dispersion units are not compatible: [{}] and [{}].".format(self.dispersion_unit, disp_unit))
                return False

        if data_unit is not None:
            if (self.unit.is_unity() or
                self.unit.is_equivalent(data_unit,
                                        equivalencies=spectral_density(
                                            self.masked_dispersion.data))):
                if self.unit.is_unity():
                    self._unit = data_unit

                self._data = self.masked_data.data.to(
                    data_unit, equivalencies=spectral_density(
                        self.masked_dispersion.data)).value

                if self._uncertainty is not None:
                    self._uncertainty = self._uncertainty.__class__(
                        self.raw_uncertainty.data.to(
                            data_unit, equivalencies=spectral_density(
                                self.masked_dispersion.data)).value)

                # Finally, change the unit
                self._unit = data_unit
            else:
                logging.warning("Data units are not compatible: [{}] and [{}].".format(self.unit, data_unit))
                return False

        return True

    @classmethod
    def _evaluate(cls, layers, formula):
        """
        Parse a string into an arithmetic expression.

        Parameters
        ----------
        layers : list
            List of `Layer` objects that correspond to the given variables.
        formula : str
            A string describing the arithmetic operations to perform.
        """
        parser = Parser()

        for layer in layers:
            formula = formula.replace(layer.name,
                                      layer.name.replace(" ", "_"))

        layer_vars = {layer.name.replace(" ", "_"): layer for layer in layers}

        try:
            expr = parser.parse(formula)
        except Exception as e:
            logging.error(e)
            return

        # Extract variables
        expr_vars = expr.variables()

        # Get the intersection of the sets of variables listed in the
        #  expression and layer names of the current layer list
        union_set = set(layer_vars.keys()).intersection(set(expr_vars))

        if len(union_set) != 0:
            logging.error("Mis-match between current layer list and expression:"
                          "%s", union_set)

        try:
            result = parser.evaluate(expr.simplify({}).toString(), layer_vars)
            result._dispersion = np.copy(layers[0]._dispersion)
            result._dispersion_unit = Unit(layers[0]._dispersion_unit)

            # Make sure layer name is unique
            i = 1

            for layer in layers:
                if layer.name == result.name:
                    result.name = result.name + "{}".format(i)
                    i += 1

        except Exception as e:
            logging.error("While evaluating formula: %s", e)
            return

        return result


class Spectrum1DRefModelLayer(Spectrum1DRefLayer):
    """
    A layer for spectrum with a model applied.

    Parameters
    ----------
    data: numpy.ndarray
        The flux.

    model: `~astropy.modeling`
        The model

    args, kwargs:
        Arguments passed to the
        `~spectutils.core.generic.Spectrum1DRef` object.
    """
    def __init__(self, data, model=None, *args, **kwargs):
        super(Spectrum1DRefModelLayer, self).__init__(data, *args,
                                                      **kwargs)
        self._model = model

    @classmethod
    def from_parent(cls, parent, model=None, layer_mask=None, copy=False):
        """
        Create a duplicate child layer from a parent layer

        Parameters
        ----------
        parent: layer
            The layer to duplicate.

        model: `~astropy.modeling`
            The model.

        layer_mask: layer
            The layer defining the valid data mask.

        copy : bool
            Copy the model if one is provided.

        Returns
        -------
        child_layer:
            The new layer.
        """
        if model is not None:
            if copy:
                model = model.copy()

            data = model(parent.masked_dispersion.data.value)
        else:
            data = np.zeros(parent.masked_dispersion.shape)

        uncertainty = parent.uncertainty.__class__(np.zeros(parent.masked_data.shape))

        return cls(name=parent.name + " Model Layer", data=data,
                   unit=parent.unit, uncertainty=uncertainty,
                   mask=parent.mask, wcs=parent.wcs,
                   dispersion=parent.masked_dispersion,
                   dispersion_unit=parent.dispersion_unit,
                   layer_mask=layer_mask or parent.layer_mask,
                   parent=parent, model=model,
                   copy=False)

    @classmethod
    def from_formula(cls, models, formula):
        """
        Create a layer from an operation performed on other models

        Parameters
        ----------
        formula: str
            The operation to perform on the given layers.

        models: [model, ...]
            The models which are arguments to the given formula.

        Returns
        -------
        result_model:
            Result of the operation
        """
        result_model = cls._evaluate(models, formula)

        return result_model

    @property
    def unmasked_data(self):
        """
        Flux quantity with no layer mask applied. Use the parent layer
        mask for cases wherein a slice of the spectrum is being used.
        """
        data = np.ma.array(
            _make_quantity(self._data, unit=self.unit),
            mask=self.parent_mask)

        return data

    @property
    def unmasked_dispersion(self):
        """
        Dispersion quantity with no layer mask applied. Use the parent layer
        mask for cases wherein a slice of the spectrum is being used.
        """
        self._dispersion = super(Spectrum1DRefLayer, self).dispersion

        dispersion = np.ma.array(
            _make_quantity(self._dispersion, unit=self.dispersion_unit),
            mask=self.parent_mask)

        return dispersion

    @property
    def unmasked_raw_uncertainty(self):
        """
        Flux uncertainty with mask applied. Returns a masked array
        containing a Quantity object. Use the parent layer mask for cases
        wherein a slice of the spectrum is being used.
        """
        uncertainty = np.ma.array(
            _make_quantity(self._uncertainty.array, unit=self.unit),
            mask=self.parent_mask)

        return uncertainty

    @property
    def parent_mask(self):
        """
        A bitwise combination of the data mask and the
        `Spectrum1DRefModelLayer`'s parent's layer mask. This is useful
        when dealing with slices of spectra in which you want the model
        layer to be the visible size of the parent *in all cases* (whereas
        `full_mask` will always be the selected region)*[]:

        Returns
        -------

        """
        if self.mask is None or self._parent is None or self._parent.layer_mask is None:
            return np.zeros(self._data.shape)

        return self.mask.astype(bool) | ~self._parent.layer_mask.astype(bool)

    @property
    def model(self):
        """Spectrum model."""
        return self._model

    @model.setter
    def model(self, value):
        self._model = value

        if self._model is not None:
            self._data = self._model(self.masked_dispersion.data.value)

    @classmethod
    def _evaluate(cls, models, formula):
        """
        Parse a string into an arithmetic expression.

        Parameters
        ----------
        models : list
            List of `Layer` objects that correspond to the given variables.
        formula : str
            A string describing the arithmetic operations to perform.
        """
        try:
            parser = Parser()
            expr = parser.parse(formula)
        except:
            return

        # Extract variables
        vars = expr.variables()

        # List the models in the same order as the variables
        sorted_models = [m for v in vars for m in models if m.name == v]

        if len(sorted_models) > len(vars):
            logging.error("Incorrect model arithmetic formula: the number "
                          "of models does not match the number of variables.")
            return
        elif len(sorted_models) < len(vars):
            extras = [x for x in vars if x not in [y.name for y in
                                                   sorted_models]]

            for extra in extras:
                matches = re.findall(
                    '([\+\*\-\/]?\s?{})'.format(extra), formula
                )

                for match in matches:
                    formula = formula.replace(match, "")

            try:
                expr = parser.parse(formula)
                vars = expr.variables()
            except:
                logging.error("An error occurred.")
                return

        try:
            result = parser.evaluate(expr.simplify({}).toString(),
                                     dict(pair for pair in
                                          zip(vars, sorted_models)))

            return result
        except (AttributeError, TypeError) as e:
            logging.error("Incorrectly formatted model formula: %s", e)
