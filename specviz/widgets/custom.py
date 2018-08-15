import pyqtgraph as pg
from qtpy.QtCore import Qt, Signal


class LinearRegionItem(pg.LinearRegionItem):
    selected = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(LinearRegionItem, self).__init__(*args, **kwargs)
        self._selected = False

        # Define the selected region color
        self._default_brush = pg.mkBrush((200, 200, 200, 100))
        self._selected_brush = self.brush
        self.setBrush(self._default_brush)

        # Tie the name property of this class to the region values
        self.sigRegionChanged.connect(self._on_region_changed)

        # Change text item visibility on selection events
        self.selected.connect(self._on_region_selected)

    def _on_region_changed(self):
        self.selected.emit(True)

    def _on_region_selected(self, state):
        self._selected = state

        if state:
            self.setBrush(self._selected_brush)
            self.update()
        else:
            self.setBrush(self._default_brush)
            self.update()

    @property
    def name(self):
        return self._name

    def mouseClickEvent(self, ev):
        super(LinearRegionItem, self).mouseClickEvent(ev)

        if ev.button() == Qt.LeftButton:
            if not self._selected:
                self.selected.emit(True)

    def mouseDragEvent(self, ev):
        super(LinearRegionItem, self).mouseDragEvent(ev)

        if not self._selected:
            self.selected.emit(True)
