from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Signal, Slot, QObject

from specutils import Spectrum1D
from astropy.io import registry as io_registry


class Hub(QObject):
    """
    Centralized event processing for interfacing with signal/slots outside the
    normal hierarchy of Qt widgets.
    """
    plot_added = Signal()
    plot_removed = Signal()

    data_added = Signal()
    data_removed = Signal()

    def __init__(self, *args, **kwargs):
        super(Hub, self).__init__(*args, **kwargs)

        self._current_window = self.parent()

    @property
    def current_model(self):
        """
        Retrieve the current model of the currently active workspace.
        """
        return self.current_window.workspace.proxy_model

    @property
    def current_window(self):
        """
        Retrieve the currently active window.
        """
        return self._current_window

    def load_data(self, path):
        pass

    def data_loader_formats(self):
        return io_registry.get_formats(Spectrum1D)['Format']
