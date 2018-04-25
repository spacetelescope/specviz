from qtpy.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QFrame, QMenu,
                            QStatusBar, QMenuBar, QMdiArea)
from qtpy.QtCore import Qt, QSize
from qtpy.QtGui import QBrush, QColor
from qtpy.uic import loadUi
import os

from ..core.events import dispatch, dispatch
from ..core.data import Spectrum1DRefLayer
from .sub_windows import PlotSubWindow
from ..widgets.utils import UI_PATH


class MainWindow(QMainWindow):
    def __init__(self, parent=None, menubar=True, *args, **kwargs):
        super(MainWindow, self).__init__(parent)

        dispatch.setup(self)

        loadUi(os.path.join(UI_PATH, "main_window.ui"), self)

        if menubar:
            self.menu_bar = self.menuBar()
        else:
            self.menu_bar = None

        self.mdi_area.subWindowActivated.connect(self._set_activated_window)

    def _set_activated_window(self, window):
        if window is None:
            all_sws = self.mdi_area.subWindowList(order=self.mdi_area.ActivationHistoryOrder)

            if len(all_sws) > 0:
                window = all_sws[-1]
            else:
                window = None

        dispatch.on_activated_window.emit(
            window=window.widget() if window is not None else None)

    @dispatch.register_listener("on_add_window")
    def add_sub_window(self, data=None, layer=None, window=None, style=None, vertical_line=False):
        layer = layer or Spectrum1DRefLayer.from_parent(data)
        is_new_window = window is None
        window = window or PlotSubWindow(vertical_line=vertical_line)

        dispatch.on_add_layer.emit(layer=layer, window=window, style=style)
        window.setWindowTitle(layer.name)

        if window is not None and is_new_window:
            mdi_sub_window = self.mdi_area.addSubWindow(window)
            window.show()
            self._set_activated_window(mdi_sub_window)

            if self.mdi_area.viewMode() == self.mdi_area.TabbedView:
                window.showMaximized()

    @dispatch.register_listener("on_add_to_window")
    def add_to_window(self, data=None, layer=None, window=None, style=None, vertical_line=False):
        # Find any sub windows currently active
        window = window or next((x.widget() for x in self.mdi_area.subWindowList(
            order=self.mdi_area.ActivationHistoryOrder)), None)

        self.add_sub_window(data=data, layer=layer, window=window, style=style, vertical_line=vertical_line)

    @dispatch.register_listener("on_add_roi")
    def add_roi(self, bounds=None, *args, **kwargs):
        mdi_sub_window = self.mdi_area.activeSubWindow() or next((x for x in self.mdi_area.subWindowList(
            order=self.mdi_area.ActivationHistoryOrder)), None)

        if mdi_sub_window is not None:
            window = mdi_sub_window.widget()
            window.add_roi(bounds=bounds)

    def get_roi_bounds(self):
        sw = self.mdi_area.activeSubWindow().widget()

        return sw.get_roi_bounds()

    @dispatch.register_listener("on_status_message")
    def update_message(self, message, timeout=0):
        self.status_bar.showMessage(message, timeout)

    def closeEvent(self, event):
        dispatch.on_dismiss_linelists_window.emit(close=True)


class MdiArea(QMdiArea):
    def __init__(self, *args, **kwargs):
        super(MdiArea, self).__init__(*args, **kwargs)

    def dragEnterEvent(self, e):
        if True:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        dispatch.on_add_window.emit(data=e.mimeData.masked_data())
