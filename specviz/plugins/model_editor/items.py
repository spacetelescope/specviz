import numpy as np

from ...core.items import DataItem


class ModelDataItem(DataItem):
    def __init__(self, model, *args, **kwargs):
        self._model_editor_model = model
        self._selected_data = None

        super().__init__(*args, **kwargs)

    @property
    def flux(self):
        if self.model_editor_model is None:
            return super().flux

        result = self.model_editor_model.evaluate()

        if result is not None:
            flux = result(self.spectral_axis.value) * self.data(self.DataRole).flux.unit
            self.data(self.DataRole)._data = flux.value
        else:
            self.data(self.DataRole)._data = np.zeros_like(self.data(self.DataRole)._data)

        return self.data(self.DataRole).flux

    @property
    def spectrum(self):
        flux = self.flux  # Update the flux
        return super().spectrum

    @property
    def model_editor_model(self):
        return self._model_editor_model

    @model_editor_model.setter
    def model_editor_model(self, value):
        self._model_editor_model = value