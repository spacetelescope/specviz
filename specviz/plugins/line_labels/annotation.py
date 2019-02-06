from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from pyqtgraph import functions, TextItem

from qtpy.QtCore import QPointF, QRectF
from qtpy.QtGui import QPolygonF, QPen, QColor

orientations = {
    'horizontal': {'anchor': (0.5, 1), 'angle': 0},
    'vertical': {'anchor': (0, 0.5), 'angle': 90}
}

__all__ = ['LineIDMarkerProxy', 'LineIDMarker']


class LineIDMarkerProxy(object):
    """
    A proxy class that is used in lieu of a real, full-blown Line1DMarker.

    The LineIDMarker constructor calls pyqtgraph's TextItem constructor.
    Profiling analysis showed that it's an expensive operation to perform.
    However, it has to be called many times during the course of a zoom
    operation. This proxy, by avoiding to call the Line1DMarker base
    class' constructor, speeds up the entire process.

    The idea is that this proxy is used to perform all the de-cluttering
    and explicit clipping operations that take place before an actual
    marker can be added to the plot. By postponing the instantiation of
    full-blown Line1DMarker objects for the very end, only the ones
    actually showing up on screen are instantiated. This saves an enormous
    amount of time not only on the constructor phase, but also on the
    addItem and removeItem calls, which seem to generate in turn an
    inordinate amount of calls to connect() and disconnect().

    Parameters:
    ----------
    x0,y0: float
        Coordinates for the marker
    marker: LineIDMarkerProxy
        A marker proxy from which to build this marker
    text: str
        The marker text
    tip: str
        The marker tool tip
    color: tuple (int, int, int)
        The marker color in RGB values
    orientation: str
        The marker orientation on screen
    """
    def __init__(self, x0, y0, proxy=None, text=None, tip="", color=(0, 0, 0),
                 orientation='horizontal'):

        self.x0 = x0
        self.y0 = y0

        if proxy:
            # complete initialization by taking
            # parameters from another instance.
            self._text = proxy._text
            self._tooltip = proxy._tooltip
            self._color = proxy._color
            self._orientation = proxy._orientation

        else:
            # initialize from passed values.
            self._text = text
            self._tooltip = tip
            self._color = color
            self._orientation = orientation

    def __str__(self):
        return str(self._text)


class LineIDMarker(TextItem):
    """
    Class that handles the drawing of a modified TextItem that's
    augmented with a linear vertical marker. These items are used
    to generate spectral line ID markers on the plot surface.

    Note the convoluted handling of the 'color' parameter. This is
    due to a bug in pyqtgraph's function 'functions.mkColor', which
    bombs when presented with an argument of type Qt.GlobalColor.

    Line1DMarker instances can only be built from instances of the
    matching Line1DMarkerProxy class, or from instances of itself.

    Parameters:
    ----------
    marker: LineIDMarkerProxy
        A marker proxy from which to build this marker
    """
    def __init__(self, marker=None):

        self.x0 = marker.x0
        self.y0 = marker.y0

        self._text = marker._text
        self._orientation = marker._orientation
        self._color = marker._color

        self._anchor = orientations[self._orientation]['anchor']
        self._angle = orientations[self._orientation]['angle']

        super(LineIDMarker, self).__init__(text=self._text, color=self._color,
                                           anchor=self._anchor,
                                           angle=self._angle)

        self._tooltip = marker._tooltip
        self.setToolTip(marker._tooltip)

        self.setFlag(self.ItemIsMovable)

    def __str__(self):
        return str(self._text)

    # Repositioning the line labels on the fly, as the data is zoomed or
    # panned, does not work. The behavior that is described in the PyQt
    # documentation is not observed. It appears that the
    # setFlags(ItemSendsGeometryChanges) does not work. I am using pyqt
    # version 4.8, so support for this flag should be there. The
    # ItemIgnoresTransformations flag doesn't work either. When set, it messes
    # up with the entire plot. This could be due to interference with
    # pyqtgraph, or a threading issue. We give up on this approach and let the
    # caller handle the zoom requests and the repainting.

    def paint(self, p, *args):
        """
        Overrides the default implementation so as
        to draw a vertical marker below the text.
        """
        # draw the text first.
        #
        # Note that this actually doesn't work. Commenting out this call to
        # the base class doesn't prevent the text to be painted on screen
        # regardless. Tests with the base class itself prove that the base
        # class paint() is not responsible for painting the text. Even when
        # the base class' code in its paint() method is replaced by a sole
        # 'pass' statement, the text still shows up on the plot. Thus there is
        # something else in either pyqtgraph or pyqt that paints the text even
        # though the entire painting mechanism in the classes is disabled.
        super(LineIDMarker, self).paint(p, args)

        # Add marker. Geometry depends on the
        # text being vertical or horizontal.
        points = []

        # get the text-only bounding rectangle.
        bounding_rect = super(LineIDMarker, self).boundingRect()

        if self._orientation == 'vertical':
            x = bounding_rect.x()
            y = bounding_rect.y() + bounding_rect.height() / 2.

            points.append(QPointF(x, y))
            points.append(QPointF(x - 20, y))
        else:
            x = bounding_rect.x() + bounding_rect.width() / 2.
            y = bounding_rect.y() + bounding_rect.height() * 2.

            points.append(QPointF(x, y))
            points.append(QPointF(x, y - 20))

        polygon = QPolygonF(points)

        pen = QPen(QColor(functions.mkColor(self._color)))
        p.setPen(pen)
        p.drawPolygon(polygon)

    def boundingRect(self):
        """
        Accounts for the fact that the modified text item has an extra
        appendage (the marker) that makes its bounding rectangle be a bit
        higher than the text-only rectangle. This is called whenever erasing
        or redrawing a line label.

        :return: QRectF
            The bounding rectangle
        """
        base_rect = super(LineIDMarker, self).boundingRect()

        if self._orientation == 'vertical':
            return QRectF(base_rect.x() - 20, base_rect.y(),
                          base_rect.width(), base_rect.height())
        else:
            return QRectF(base_rect.x(), base_rect.y() - 20,
                          base_rect.width(), base_rect.height())
