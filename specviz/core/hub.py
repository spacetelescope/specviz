# from qtpy.QtWidgets import QObject
from qtpy.QtCore import Signal, Slot, QObject


class Hub(QObject):
    plot_added = Signal()
    plot_removed = Signal()
    data_added = Signal()
    data_removed = Signal()