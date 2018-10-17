import pyqtgraph as pg
from qtpy.QtCore import Qt, Signal, QSize
from qtpy.QtWidgets import QTabBar, QPushButton


class LinearRegionItem(pg.LinearRegionItem):
    selected = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(LinearRegionItem, self).__init__(*args, **kwargs)
        self._selected = False

        # Define the selected region color
        self._default_brush = pg.mkBrush((200, 200, 200, 75))
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


class TabBarPlus(QTabBar):
    """Tab bar that has a plus button floating to the right of the tabs."""

    plusClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Plus Button
        self.plusButton = QPushButton("+")
        self.plusButton.setParent(self)
        self.plusButton.setFixedSize(20, 20)  # Small Fixed size
        self.plusButton.clicked.connect(self.plusClicked.emit)
        self.movePlusButton() # Move to the correct location
    # end Constructor

    def sizeHint(self):
        """Return the size of the TabBar with increased width for the plus button."""
        sizeHint = QTabBar.sizeHint(self)
        width = sizeHint.width()
        height = sizeHint.height()
        return QSize(width+25, height)
    # end tabSizeHint

    def resizeEvent(self, event):
        """Resize the widget and make sure the plus button is in the correct location."""
        super().resizeEvent(event)

        self.movePlusButton()
    # end resizeEvent

    def tabLayoutChange(self):
        """This virtual handler is called whenever the tab layout changes.
        If anything changes make sure the plus button is in the correct location.
        """
        super().tabLayoutChange()

        self.movePlusButton()
    # end tabLayoutChange

    def movePlusButton(self):
        """Move the plus button to the correct location."""
        # Find the width of all of the tabs
        size = sum([self.tabRect(i).width() for i in range(self.count())])
        # size = 0
        # for i in range(self.count()):
        #     size += self.tabRect(i).width()

        # Set the plus button location in a visible area
        h = self.geometry().top()
        w = self.width()
        if size > w: # Show just to the left of the scroll buttons
            self.plusButton.move(w-54, h)
        else:
            self.plusButton.move(size, h)