from qtpy.QtCore import QThread, Signal


class OperationThread(QThread):
    """
    Thread in which an operation is performed on some
    :class:`~spectral_cube.SpectralCube` object to ensure that the UI does not
    freeze while the operation is running.

    Attributes
    ----------
    cube_data : :class:`~spectral_cube.SpectralCube`
        The cube data on which the operation will be performed.
    function : callable
        The function-like callable used to perform the operation on the cube.
    """
    status = Signal(float)
    finished = Signal(object, str)

    def __init__(self, data, function, parent=None):
        super(OperationThread, self).__init__(parent)
        self._data = data
        self._function = function
        self._tracker = SimpleProgressTracker(self._data.shape[1] * self._data.shape[2],
                                              status=self.status)

    def run(self):
        """Run the thread."""
        new_data, unit = self._function(self._data, self._tracker)

        self.finished.emit(new_data, unit)

    def abort(self):
        """
        Abort the operation. Halts and returns immediately by raising an
        error.
        """
        self._tracker.abort()


class SimpleProgressTracker():
    """
    Simple container object to track the progress of an operation occuring in a
    :class:`~qtpyt.QtCore.QThread` instance. It is designed to be passed to
    :class:`~spectral_cube.SpectralCube` object to be called while performing
    operations.

    Attributes
    ----------
    total_value : float
        The maximum value of the progress.
    """

    def __init__(self, total_value, status=None):
        self._current_value = 0.0
        self._total_value = total_value
        self._abort_flag = False
        self._status = status

    def __call__(self, value=None):
        self._current_value = value or self._current_value + 1

        if self._status is not None:
            self._status.emit(self.percent_value)

        if self._abort_flag:
            raise Exception("Process aborted.")

    @property
    def percent_value(self):
        """Return the completion amount as a percentage."""
        return self._current_value / self._total_value

    def abort(self):
        """
        Set the abort flag which will raise an error causing the operation
        to return immediately.
        """
        self._abort_flag = True
