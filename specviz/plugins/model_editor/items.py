import numpy as np

from astropy import units as u

from specutils.spectra import Spectrum1D

from ...core.items import DataItem


class ModelDataItem(DataItem):
    def __init__(self, model, *args, **kwargs):
        self._model_editor_model = model

        self._plot_data_item = None

        self._special_args = {}

        super().__init__(*args, **kwargs)

    @property
    def flux(self):
        if self.model_editor_model is None:
            return super().flux

        result = self.model_editor_model.evaluate()

        flux_units = self.data(self.DataRole).flux.unit

        if self._plot_data_item is None:
            model_flux_units = flux_units
        else:
            model_flux_units = u.Unit(self._plot_data_item.data_unit)

        if result is not None:
            model_flux = result(self.model_spectral_axis.value) * model_flux_units
            return model_flux.to(flux_units,
                                 equivalencies=u.equivalencies.spectral_density(
                                     self.model_spectral_axis))

        return np.zeros(self.spectral_axis.size) * model_flux_units

    @property
    def model_spectral_axis(self):
        if self._plot_data_item is None:
            model_spectral_units = self.data(self.DataRole).spectral_axis.unit
        else:
            model_spectral_units = u.Unit(self._plot_data_item.spectral_axis_unit)
        return self.spectral_axis.to(model_spectral_units,
                                     equivalencies=u.equivalencies.spectral())

    @property
    def model_editor_model(self):
        return self._model_editor_model

    @model_editor_model.setter
    def model_editor_model(self, value):
        self._model_editor_model = value

    @property
    def spectrum(self):
        return Spectrum1D(flux=self.flux, spectral_axis=self.model_spectral_axis)
