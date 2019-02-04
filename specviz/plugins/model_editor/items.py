import numpy as np

from ...core.items import DataItem


class ModelDataItem(DataItem):
    """
    Data container for information generated from a model editor model's
    collection of models. This provides an interface to the generated flux
    values of the model evaluated in the model editor model.

    Parameters
    ----------
    model : :class:`specviz.plugins.model_editor.models.ModelFittingModel`
        The model edtior fitting model containing the list of individual models
        used in the editor, as well as the equation to evaluate for model
        arithmetic.
    """
    def __init__(self, model, *args, **kwargs):
        self._model_editor_model = model
        self._selected_data = None

        super().__init__(*args, **kwargs)

    @property
    def flux(self):
        """
        Evaluates the current model editor model equation, generates and
        returns new flux values, and updates the stored spectrum information.
        """
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
        """
        The internal spectrum object.
        """
        return super().spectrum

    @property
    def model_editor_model(self):
        """
        The model editor model used during evaluation of the flux.
        """
        return self._model_editor_model

    @model_editor_model.setter
    def model_editor_model(self, value):
        self._model_editor_model = value
