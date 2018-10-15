from ...core.items import DataItem
import astropy.units as u


class ModelDataItem(DataItem):
    def __init__(self, model, *args, **kwargs):
        self._model_editor_model = model

        super().__init__(*args, **kwargs)

    @property
    def flux(self):
        if self.model_editor_model is None:
            return super().flux

        result = self.model_editor_model.evaluate()

        return result(self.spectral_axis.value) * self.data(self.DataRole).flux.unit

    @property
    def model_editor_model(self):
        return self._model_editor_model

    @model_editor_model.setter
    def model_editor_model(self, value):
        self._model_editor_model = value