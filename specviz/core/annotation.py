from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from pyqtgraph import functions, TextItem

from qtpy.QtCore import QPointF
from qtpy.QtGui import QPolygonF, QPen, QColor

orientations = {
    'horizontal': {'anchor': (0.5, 1), 'angle': 0},
    'vertical': {'anchor': (0, 0.5), 'angle': 90}
}


class LineIDMarkerProxy(object):
    ''' A proxy class that is used in lieu of a real, full-blown Line1DMarker.

        The LineIDMarker constructor calls pyqtgraph's TextItem constructor. Profiling
        analysis showed that it's an expensive operation to perform. However, it has
        to be called many times during the course of a zoom operation. This proxy,
        by avoiding to call the Line1DMarker base class' constructor, speeds up
        the entire process.

        The idea is that this proxy is used to perform all the de-cluttering and
        explicit clipping operations that take place before an actual marker can
        be added to the plot. By postponing the instantiation of full-blown Line1DMarker
        objects for the very end, only the ones actually showing up on screen are
        instantiated. This saves an enormous amount of time not only on the constructor
        phase, but also on the addItem and removeItem calls, which seem to generate in
        turn an inordinate amount of calls to connect() and disconnect().
    '''

    def __init__(self, x0, y0, proxy=None, text=None, plot_item=None, tip="", color=(0, 0, 0),
                 orientation='horizontal'):

        self.x0 = x0
        self.y0 = y0

        if proxy:
            # complete initialization by taking
            # parameters from another instance.
            self._text = proxy._text
            self._plot_item = proxy._plot_item
            self._tooltip = proxy._tooltip
            self._color = proxy._color
            self._orientation = proxy._orientation

        else:
            # initialize from passed values.
            self._text = text
            self._plot_item = plot_item
            self._tooltip = tip
            self._color = color
            self._orientation = orientation

    def __str__(self):
        return str(self._text)


class LineIDMarker(TextItem):
    ''' This class handles the drawing of a modified TextItem that's
        augmented with a linear vertical marker. These items are used
        to generate spectral line ID markers on the plot surface.

        Note the convoluted handling of the 'color' parameter. This is
        due to a bug in pyqtgraph's function 'functions.mkColor', which
        bombs when presented with an argument of type Qt.GlobalColor.

        Line1DMarker instances can only be built from instances of the
        matching Line1DMarkerProxy class, or from instances of itself.
    '''

    def __init__(self, marker=None):

        self.x0 = marker.x0
        self.y0 = marker.y0

        self._text = marker._text
        self._plot_item = marker._plot_item
        self._orientation = marker._orientation
        self._color = marker._color

        self._anchor = orientations[self._orientation]['anchor']
        self._angle = orientations[self._orientation]['angle']

        super(LineIDMarker, self).__init__(text=self._text, color=self._color,
                                           anchor=self._anchor, angle=self._angle)

        self._tooltip = marker._tooltip
        self.setToolTip(marker._tooltip)

        self.setFlag(self.ItemIsMovable)

    # Repositioning the line labels on the fly, as the data is  zoomed in and out,
    # does not work. The behavior that is described in the PyQt documentation is not
    # observed. It appears that the setFlags(ItemSendsGeometryChanges) does not work.
    # I am using pyqt version 4.8, so support for this flag should be there. The
    # ItemIgnoresTransformations flag doesn't work either. When set, it messes up with
    # the entire plot. This could be due to interference with pyqtgraph, or a threading
    # issue. We give up on this approach and let the caller handle the zoom requests and
    # the repainting.

    def __str__(self):
        return str(self._text)

    def paint(self, p, *args):
        ''' Overrides the default implementation so as
            to draw a vertical marker.
        '''
        # draw the text
        #
        # Note that this actually doesn't work. Commenting out this call to the base
        # class doesn't prevent the text to be painted on screen regardless. Tests with
        # the base class itself prove that the base class paint() is not responsible for
        # painting the text. Even when the base class' code in its paint() method is
        # replaced by a sole 'pass' statement, the text still shows up on the plot.
        # Thus there is something else in either pyqtgraph or pyqt that paints the text
        # even though the entire painting mechanism in the classes is disabled.
        super(LineIDMarker, self).paint(p, args)

        # Add marker. Geometry depends on the
        # text being vertical or horizontal.
        points = []
        bounding_rect = self.boundingRect()

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


