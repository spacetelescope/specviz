import os

from qtpy.QtCore import QThread, Signal
from qtpy.QtWidgets import QDialog, QMessageBox
from qtpy.uic import loadUi
from specutils.manipulation.smoothing import (box_smooth, gaussian_smooth,
                                              median_smooth, trapezoid_smooth)

from ...core.items import PlotDataItem
from ...core.plugin import plugin

KERNEL_REGISTRY = {
    """
    Dictionary to store available kernel options.

    KERNEL_REGISTRY:
        kernel_type: Type of kernel
            name: Display name
            unit_label: Display units of kernel size (singular)
            size_dimension: Dimension of kernel (width, radius, etc..)
            function: Smoothing function
    """
    "box": {"name": "Box",
            "unit_label": "Pixel",
            "size_dimension": "Width",
            "function": box_smooth},
    "gaussian": {"name": "Gaussian",
                 "unit_label": "Pixel",
                 "size_dimension": "Std Dev",
                 "function": gaussian_smooth},
    "trapezoid": {"name": "Trapezoid",
                  "unit_label": "Pixel",
                  "size_dimension": "Width",
                  "function": trapezoid_smooth},
    "median": {"name": "Median",
               "unit_label": "Pixel",
               "size_dimension": "Width",
               "function": median_smooth}
}


@plugin("Smoothing")
class SmoothingDialog(QDialog):
    """
    Widget to handle user interactions with smoothing operations.
    Allows the user to select spectra, kernel type and kernel size.
    It utilizes smoothing functions in `~specutils.manipulation.smoothing`.
    Assigns the smoothing workload to a QTread instance.
    """
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)

        self.model_items = None

        self._smoothing_thread = None  # Worker thread

        self.kernel = None  # One of the sub-dicts in KERNEL_REGISTRY
        self.function = None  # function from `~specutils.manipulation.smoothing`
        self.data = None  # Current `~specviz.core.items.DataItem`
        self.size = None  # Current kernel size
        self._already_loaded = False

        #
        # Do the first-time loading and initialization of the GUI
        #
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "smoothing.ui")), self)

        self.smooth_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.close)
        self.data_combo.currentIndexChanged.connect(self._on_data_change)

        for key in KERNEL_REGISTRY:
            kernel = KERNEL_REGISTRY[key]
            self.kernel_combo.addItem(kernel["name"], key)
        self.kernel_combo.currentIndexChanged.connect(self._on_kernel_change)

    @plugin.tool_bar("Smoothing", location="Operations")
    def on_action_triggered(self):
        # Update the current list of available data items
        self.model_items = self.hub.data_items

        self._display_ui()
        self.exec_()

    def _display_ui(self):
        """
        Things to do each time the Smoothing GUI is re-displayed.
        """
        self.data_combo.clear()
        for index, data in enumerate(self.model_items):
            self.data_combo.addItem(data.name, index)

        self._on_data_change(0)
        self._on_kernel_change(0)

        self.set_to_current_selection()
        self.smooth_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def set_to_current_selection(self):
        """Sets Data selection to currently active data"""
        current_item = self.hub.workspace.current_item
        if current_item is not None:
            if isinstance(current_item, PlotDataItem):
                current_item = current_item.data_item
        if current_item is not None and current_item in self.model_items:
            index = self.model_items.index(current_item)
            self.data_combo.setCurrentIndex(index)

    def _on_kernel_change(self, index):
        """Callback for kernel combo index change"""
        key = self.kernel_combo.currentData()
        kernel = KERNEL_REGISTRY[key]  # Kernel type
        self.size_label.setText(kernel["size_dimension"])
        self.unit_label.setText(kernel["unit_label"]+"s")
        self.function = kernel["function"]
        self.kernel = kernel

    def _on_data_change(self, index):
        """Callback for data combo index change"""
        data_index = self.data_combo.currentData()

        if data_index is not None and len(self.model_items) > 0:
            self.data = self.model_items[data_index]

    def _generate_output_name(self):
        """Generate a name for output spectra"""
        unit_label = self.kernel["unit_label"].lower()
        unit_format = "{0} {1}" if self.size == 1. else "{0} {1}s"
        size_text = unit_format.format(self.size, unit_label)

        return "{0} Smoothed({1}, {2})".format(self.data.name, self.kernel["name"], size_text)

    def is_size_valid(self):
        """
        Check if size input is valid.
        Marks LineEdit red if input is invalid.

        returns
        -------
        bool: True if no errors
        """
        success = True
        try:
            size = float(self.size_input.text())
            if size <= 0:
                success = False
        except ValueError:
            success = False

        if success:
            self.size_input.setStyleSheet("")
        else:
            red = "background-color: rgba(255, 0, 0, 128);"
            self.size_input.setStyleSheet(red)

        return success

    def accept(self):
        """Called when the user clicks the "Smooth" button of the dialog."""
        if not self.is_size_valid():
            return

        self.smooth_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        self.size = float(self.size_input.text())

        if self.data is not None:
            self._smoothing_thread = SmoothingThread(self.data.spectrum, self.size, self.function)
            self._smoothing_thread.finished.connect(self.on_finished)
            self._smoothing_thread.exception.connect(self.on_exception)

            self._smoothing_thread.start()

    def on_finished(self, spec):
        """
        Called when the `QThread` has finished performing
        the smoothing operation.
        Parameters
        ----------
        spec : `~specutils.Spectrum1D`
            The result of the smoothing operation.
        """
        name = self._generate_output_name()
        self.hub.workspace.model.add_data(spec=spec, name=name)
        self.close()

    def on_exception(self, exception):
        """
        Called when the `QThread` runs into an exception.
        Parameters
        ----------
        exception : Exception
            The Exception that interrupted the `QThread`.
        """
        self.smooth_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

        info_box = QMessageBox(parent=self)
        info_box.setWindowTitle("Smoothing Error")
        info_box.setIcon(QMessageBox.Critical)
        info_box.setText(str(exception))
        info_box.setStandardButtons(QMessageBox.Ok)
        info_box.show()


class SmoothingThread(QThread):
    """
    Thread in which a single smoothing operation
    is performed to ensure that the UI does not
    freeze while the operation is running.

    Parameters
    ----------
    data : `~specutils.Spectrum1D`
    size : Number
        Smoothing kernel size.
    func : function
        Smoothing function from `~specutils.manipulation.smoothing`.
    parent : `~specviz.widgets.smoothing.SmoothingDialog`

    Signals
    -------
    finished : Signal
        Notifies parent UI that smoothing is complete and is used to
        communicate the resulting data.
    exception : Signal
        Sends exceptions to parent UI where they are raised.
    """
    finished = Signal(object)
    exception = Signal(Exception)

    def __init__(self, data, size, func, parent=None):
        super(SmoothingThread, self).__init__(parent)
        self._data = data
        self._size = size
        self._function = func
        self._tracker = None

    def run(self):
        """Run the thread."""
        try:
            new_spec = self._function(self._data, self._size)
            self.finished.emit(new_spec)
        except Exception as e:
            self.exception.emit(e)

