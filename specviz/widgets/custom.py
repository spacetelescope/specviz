import os

import pyqtgraph
from qtpy.QtCore import QSize, Qt, Signal
from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import QDialog, QPushButton, QTabBar
from qtpy.uic import loadUi

__all__ = ['LinearRegionItem', 'TabBarPlus', 'PlotSizeDialog']


class LinearRegionItem(pyqtgraph.LinearRegionItem):
    """
    Subclass of pyqtgraph's :class:`~pyqtgraph.LinearRegionItem` to provide extra
    methods for handling events and dealing with selection color changes.
    """
    selected = Signal(bool)

    def __init__(self, *args, **kwargs):
        super(LinearRegionItem, self).__init__(*args, **kwargs)
        self._selected = False

        # Define the selected region color
        self._default_brush = pyqtgraph.mkBrush((200, 200, 200, 75))
        self._selected_brush = self.brush
        self.setBrush(self._default_brush)

        # Tie the name property of this class to the region values
        self.sigRegionChanged.connect(self._on_region_changed)

        # Change text item visibility on selection events
        self.selected.connect(self._on_region_selected)

    def _on_region_changed(self):
        """
        Emit an extra signal indicating whether region selection is active.
        """
        self.selected.emit(True)

    def _on_region_selected(self, state):
        """When a region is selected, update the selection brush."""
        self._selected = state

        if state:
            self.setBrush(self._selected_brush)
            self.update()
        else:
            self.setBrush(self._default_brush)
            self.update()

    @property
    def name(self):
        """
        The name of this linear region item.

        Returns
        -------
        str
            Name of the region.

        """
        return self._name

    def mouseClickEvent(self, ev):
        """
        Intercepts mouse click events.

        Parameters
        ----------
        ev : :class:`~qtpy.QtGui.QMouseEvent`
            The qt event object.
        """
        super(LinearRegionItem, self).mouseClickEvent(ev)

        if ev.button() == Qt.LeftButton:
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


class PlotSizeDialog(QDialog):
    """
    Displays a modal dialog prompting the user for the exported image
    dimensions.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load the ui file and attach it to this instance
        loadUi(os.path.join(os.path.dirname(__file__),
                            "ui", "export_size.ui"), self)

        # Add some simple validators to the text boxes
        self.height_line_edit.setValidator(QIntValidator())
        self.width_line_edit.setValidator(QIntValidator())


from pyqtgraph.exporters import ImageExporter
from pyqtgraph.Qt import QtGui, QtCore, USE_PYSIDE
from pyqtgraph import functions as fn
import numpy as np


class ModifiedImageExporter(ImageExporter):
    """
    Override the current image exporter in pyqtgraph to get rid of a bug. The
    Bug is fixed in the latest development version, but not in the released
    version.
    """
    def export(self, fileName=None, toBytes=False, copy=False):
        if fileName is None and not toBytes and not copy:
            if USE_PYSIDE:
                filter = ["*." + str(f) for f in
                          QtGui.QImageWriter.supportedImageFormats()]
            else:
                filter = ["*." + bytes(f).decode('utf-8') for f in
                          QtGui.QImageWriter.supportedImageFormats()]
            preferred = ['*.png', '*.tif', '*.jpg']
            for p in preferred[::-1]:
                if p in filter:
                    filter.remove(p)
                    filter.insert(0, p)
            self.fileSaveDialog(filter=filter)
            return

        targetRect = QtCore.QRect(0, 0, self.params['width'],
                                  self.params['height'])
        sourceRect = self.getSourceRect()

        # self.png = QtGui.QImage(targetRect.size(), QtGui.QImage.Format_ARGB32)
        # self.png.fill(pyqtgraph.mkColor(self.params['background']))
        w, h = int(self.params['width']), int(self.params['height'])
        if w == 0 or h == 0:
            raise Exception(
                "Cannot export image with size=0 (requested export size is %dx%d)" % (
                w, h))
        bg = np.empty((int(self.params['width']), int(self.params['height']), 4),
                      dtype=np.ubyte)
        color = self.params['background']
        bg[:, :, 0] = color.blue()
        bg[:, :, 1] = color.green()
        bg[:, :, 2] = color.red()
        bg[:, :, 3] = color.alpha()
        self.png = fn.makeQImage(bg, alpha=True)

        ## set resolution of image:
        origTargetRect = self.getTargetRect()
        resolutionScale = targetRect.width() / origTargetRect.width()
        # self.png.setDotsPerMeterX(self.png.dotsPerMeterX() * resolutionScale)
        # self.png.setDotsPerMeterY(self.png.dotsPerMeterY() * resolutionScale)

        painter = QtGui.QPainter(self.png)
        # dtr = painter.deviceTransform()
        try:
            self.setExportMode(True, {'antialias': self.params['antialias'],
                                      'background': self.params['background'],
                                      'painter': painter,
                                      'resolutionScale': resolutionScale})
            painter.setRenderHint(QtGui.QPainter.Antialiasing,
                                  self.params['antialias'])
            self.getScene().render(painter, QtCore.QRectF(targetRect),
                                   QtCore.QRectF(sourceRect))
        finally:
            self.setExportMode(False)
        painter.end()

        if copy:
            QtGui.QApplication.clipboard().setImage(self.png)
        elif toBytes:
            return self.png
        else:
            self.png.save(fileName)
