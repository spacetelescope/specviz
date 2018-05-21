from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Signal, Slot


class Hub(QWidget):
    plot_added = Signal()
    plot_removed = Signal()
    data_added = Signal()
    data_removed = Signal()

    def __init__(self, *args, **kwargs):
        super(Hub, self).__init__(*args, **kwargs)