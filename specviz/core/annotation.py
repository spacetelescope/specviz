from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from pyqtgraph import functions, TextItem

from qtpy.QtCore import QPointF
from qtpy.QtGui import QTransform, QPolygonF, QPen, QColor


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
    def __init__(self, text, plot_item, tip="", color=(0,0,0), orientation='horizontal'):

        self._plot_item = plot_item
        self._orientation = orientation
        self._color = functions.mkColor(color)

        anchor = orientations[orientation]['anchor']
        angle = orientations[orientation]['angle']

        super(LineIDMarker, self).__init__(text=text, color=color, anchor=anchor, angle=angle)

        # self.setFlag(self.ItemIgnoresTransformations)
        self.setFlag(self.ItemIsMovable)
        self.setFlag(self.ItemSendsGeometryChanges)
        # self.setFlag(self.ItemIsMovable)
        self.setToolTip(tip)

    # TODO these are attempts to reposition the line labels on the fly, as
    # the data is zoomed in and out. Nothing works. The behavior that is
    # described in the PyQt documentation is not observed. It appears that
    # the setFlags(ItemSendsGeometryChanges) does not work. I am using pyqt
    # version 4.8, so support for this flag should be there.
    # The ItemIgnoresTransformations flag doesn't work either. When set, it
    # messes the entire plot. This could be dues to interference with pyqtgraph.
    # No way to know.

    # def itemChange(self, change, value):
    #     ret = super(LineIDMarker, self).itemChange(change, value)
    #
    #     print("@@@@@@  file annotation.py; line 43 - ",  change, value)
    #
    #     print("@@@@@@  file annotation.py; line 45 - ",  self.x(), self.y())
    #
    #     # if change == self.ItemPositionChange:
    #
    #         # print("@@@@@@  file annotation.py; line 49 -   AAAAAAA")
    #
    #         # newPos = self.scenePos()
    #
    #         # print("@@@@@@  file annotation.py; line 45 - ",  newPos)
    #
    #         # rect = self.sceneBoundingRect()
    #
    #         # newPos.setY(y)
    #
    #         # print("@@@@@@  file annotation.py; line 54 - ",  self.scenePos())
    #         # return newPos
    #         # # return ret
    #
    #         # newPos.setY(self.y() * 0.7)
    #
    #         # return newPos
    #
    #         # t = self.transform()
    #         # newT = QTransform(t)
    #         # t2 = newT.translate(0.,10.)
    #         #
    #         # print("@@@@@@  file annotation.py; line 72 - ",  newT.m22(), newT.m32())
    #         # print("@@@@@@  file annotation.py; line 73 - ",  t2.m22(), t2.m32())
    #         #
    #         # return t2
    #
    #     if hasattr(value, 'y'):
    #         return QPointF(self.pos().x(), value.y())
    #
    #
    #
    #         # return ret
    #
    #     return ret

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
