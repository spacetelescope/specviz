import os
import numpy as np

from qtpy.QtWidgets import QDialog, QDialogButtonBox
from qtpy.uic import loadUi
from spectral_cube import BooleanArrayMask, SpectralCube
from glue.core import Subset, Data

from ...widgets.utils import ICON_PATH, UI_PATH
from .threads import OperationThread


class SpectralOperationHandler(QDialog):
    """
    Widget to handle user interactions with operations that are communicated
    from the SpecViz viewer. This is built to work with
    :func:`~spectral_cube.SpectralCube.apply_function` method by passing in a
    callable :class:`specviz.analysis.operations.FunctionalOperation` object.

    Attributes
    ----------
    data : :class:`~glue.core.data.Data`
        Glue data object on which the spectral operation will be performed.
    function : :class:`specviz.analysis.operations.FunctionalOperation`
        Python class instance whose `call` function will be performed on the
        :class:`~spectral_cube.SpectralCube` object.
    """

    def __init__(self, data, function, operation_name, component_id, layout,
                 ui_settings=None, *args, **kwargs):
        super(SpectralOperationHandler, self).__init__(*args, **kwargs)
        self._data = data
        self._function = function
        self._operation_name = operation_name
        self._component_id = component_id
        self._operation_thread = None
        self._layout = layout
        self._ui_settings = ui_settings

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Setup the PyQt UI for this dialog."""
        # Load the ui dialog
        loadUi(os.path.join(os.path.dirname(__file__), "apply_operation.ui"), self)

        if self._ui_settings is not None:
            self.setWindowTitle(self._ui_settings.get("title"))
            self.operation_group_box.setTitle(self._ui_settings.get("group_box_title"))
            self.description_label.setText(self._ui_settings.get("description"))

        component_ids = [str(i) for i in self._data.component_ids()]
        cur_ind = self._data.component_ids().index(self._component_id)

        self.operation_combo_box.addItem(self._operation_name)

        # Populate combo box
        self.data_component_combo_box.addItems(component_ids)
        self.data_component_combo_box.setCurrentIndex(cur_ind)

        # Disable the button box if there are no available operations
        if self._function is None:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def setup_connections(self):
        """Setup signal/slot connections for this dialog."""
        # When a data component is selected, update the data object reference
        self.data_component_combo_box.currentIndexChanged.connect(
            self.on_data_component_index_changed)

        # If the abort button is clicked, attempted to stop execution
        self.abort_button.clicked.connect(self.on_aborted)

    def _compose_cube(self):
        """
        Create a :class:`~spectral_cube.SpectralCube` from a Glue data
        component.
        """
        if issubclass(self._data.__class__, Subset):
            wcs = self._data.data.coords.wcs
            data = self._data.data
            mask = self._data.to_mask()
        else:
            wcs = self._data.coords.wcs
            data = self._data
            mask = np.ones(self._data.shape).astype(bool)

        mask = BooleanArrayMask(mask=mask, wcs=wcs)

        return SpectralCube(data[self._component_id], wcs=wcs, mask=mask)

    def on_data_component_index_changed(self, index):
        """Called when the index of the component combo box has changed."""
        self._component_id = self._data.component_ids()[index]

    def accept(self):
        """Called when the user clicks the "Okay" button of the dialog."""
        # Show the progress bar and abort button
        self.progress_bar.setEnabled(True)
        self.abort_button.setEnabled(True)

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QDialogButtonBox.Cancel).setEnabled(False)

        self._operation_thread = OperationThread(self._compose_cube(),
                                                 self._function)

        self._operation_thread.finished.connect(self.on_finished)
        self._operation_thread.status.connect(self.on_status_updated)
        self._operation_thread.start()

    def on_aborted(self):
        """Called when the user aborts the operation."""
        self._operation_thread.abort()
        self.progress_bar.setValue(0)

        # Hide the progress bar and abort button
        self.abort_button.setEnabled(False)

        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        self.button_box.button(QDialogButtonBox.Cancel).setEnabled(True)

    def on_status_updated(self, value):
        """
        Called when the status of the operation has been updated. This can be
        optionally be passed a value to use as the new progress bar value.

        Attributes
        ----------
        value : float
            The value passed to the :class:`~qtpy.QtWidgets.QProgressBar`
            instance.
        """
        self.progress_bar.setValue(value * 100)

    def on_finished(self, data):
        """
        Called when the `QThread` has finished performing the operation on the
        `SpectralCube` object.

        Attributes
        ----------
        data : ndarray
            The result of the operation performed on the `SpectralCube` object.
        """
        component_name = "{} {}".format(self._component_id,
                                        self._operation_name)

        comp_count = len([x for x in self._data.component_ids()
                          if component_name in str(x)])

        if comp_count > 0:
            component_name = "{} {}".format(component_name, comp_count)

        if len(data.shape) == len(self._data.shape):
            self._layout.add_overlay(data[0, :, :], component_name, display_now=False)

        self._data.add_component(data, component_name)

        super(SpectralOperationHandler, self).accept()
