from specviz.core.plugin import plugin

from specutils.fitting import fit_generic_continuum
from specutils import Spectrum1D

from .items import ModelDataItem
from .models import ModelFittingModel
import uuid


@plugin("Continuum Generator")
class ContinuumGenerator:
    """
    Auto-generates a continuum using the specutils
    :func:`~specutils.fitting.fit_generic_continuum` function.
    """
    @plugin.tool_bar("Generate continuum model", location="Operations")
    def on_action_triggered(self):
        """
        The action triggered via interaction with the UI. Generates the
        continuum for the selected regions on the spectrum.
        """
        # Get the currently selected data item
        spec = self.hub.data_item.spectrum

        # Retrieve any rois to be used for exclusion in the continuum fit.
        inc_regs = self.hub.spectral_regions
        exc_regs = inc_regs.invert_from_spectrum(spec) \
            if inc_regs is not None else None

        # Perform the continuum fitting, storing both model and array output
        cont_mod = fit_generic_continuum(spec, exclude_regions=exc_regs)
        y_cont = cont_mod(spec.spectral_axis)

        # Construct the new spectrum object containing the array
        new_spec = Spectrum1D(flux=y_cont, spectral_axis=spec.spectral_axis)

        # Add the continuum model to the model data item's fitting model
        model_fitting_model = ModelFittingModel()
        model_fitting_model.add_model(cont_mod.unitless_model)

        # Create a new model data item to be added to the data list
        model_data_item = ModelDataItem(model=model_fitting_model,
                                        name="Continuum (auto-generated)",
                                        identifier=uuid.uuid4(),
                                        data=new_spec)

        # Add the model data item to the internal qt model
        self.hub.append_data_item(model_data_item)
