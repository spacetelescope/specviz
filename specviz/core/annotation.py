from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from pyqtgraph import functions, TextItem

from qtpy.QtCore import QPointF
from qtpy.QtGui import QPolygonF, QPen, QColor


orientations = {
    'horizontal': {'anchor': (0.5, 1), 'angle': 0},
    'vertical':   {'anchor': (0, 0.5), 'angle': -90}
}


class LineIDMarker(TextItem):
    ''' This class handles the drawing of a modified TextItem that's
        augmented with a linear vertical marker. These items are used
        to generate spectral line ID markers on the plot surface.

        Note the convoluted handling of the 'color' parameter. This is
        due to a bug in pyqtgraph's function 'functions.mkColor', which
        bombs when presented with an argument of type Qt.GlobalColor.
    '''
    def __init__(self, marker=None, text=None, plot_item=None, tip="", color=(0,0,0), orientation='horizontal'):

        if marker == None:
            self._text = text
            self._plot_item = plot_item
            self._orientation = orientation
            self._color = color

            self._anchor = orientations[orientation]['anchor']
            self._angle = orientations[orientation]['angle']

            super(LineIDMarker, self).__init__(text=text, color=color, anchor=self._anchor, angle=self._angle)

            self._tooltip = tip
            self.setToolTip(tip)

        else:
            self._text = marker._text
            self._plot_item = marker._plot_item
            self._orientation = marker._orientation
            self._color = marker._color

            self._anchor = marker._anchor
            self._angle = marker._angle

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
