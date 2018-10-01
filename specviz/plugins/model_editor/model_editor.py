import os

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget, QMessageBox
from qtpy.uic import loadUi

from .equation_editor_dialog import ModelEquationEditorDialog
from .models import ModelFittingModel
from ...core.plugin import Plugin, plugin_bar

from specutils.spectra import Spectrum1D
from specutils.fitting import fit_lines


@plugin_bar("Model Editor", icon=QIcon(":/icons/012-file.svg"))
class ModelEditor(QWidget, Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "model_editor.ui")), self)

        # Instantiate the model fitting model
        self._model_fitting_model = ModelFittingModel()

        # Set the model on the tree view and expand all children initially.
        self.model_tree_view.setModel(self._model_fitting_model)
        self.model_tree_view.expandAll()

        # Store a reference to the equation editor dialog. This way, after a
        # user has closed the dialog, the state of the text edit box will be
        # preserved.
        self._equation_dialog = ModelEquationEditorDialog(
                self._model_fitting_model)

        self.equation_editor_button.clicked.connect(
            self._equation_dialog.exec_)

        # When the equation editor dialog input is accepted, create the
        self._equation_dialog.accepted.connect(
            lambda: self._on_equation_accepted(self._equation_dialog.result))

    def _on_equation_accepted(self, result):
        if self.data_item is None:
            message_box = QMessageBox()
            message_box.setText("No item selected, cannot fit model.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "There is currently no item selected. Please select an item "
                "before attempting to fit the model.")

            message_box.exec()
            return

        # Create a new spectrum1d object and add it to the view
        fit_mod = fit_lines(self.data_item.spectrum, result)
        new_spec = Spectrum1D(flux=fit_mod(self.data_item.spectrum.spectral_axis),
                              spectral_axis=self.data_item.spectrum.spectral_axis)
        self.model.add_data(new_spec, "Fitted Model Spectrum")
        self.plot_widget.autoRange()