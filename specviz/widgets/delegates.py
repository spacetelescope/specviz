from qtpy.QtCore import Qt, QPoint, QRect, QSize
from qtpy.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem
from qtpy.QtGui import QPixmap
import qtawesome as qta


class DataItemDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(DataItemDelegate, self).__init__(*args, **kwargs)
        self.padding = 2

    def paint(self, painter, option, index):
        # option.decorationAlignment = Qt.AlignRight
        option.decorationPosition = QStyleOptionViewItem.Left

        super().paint(painter, option, index)
        # x = option.rect.x()
        # y = option.rect.y()
        # width = option.rect.width()
        # height = option.rect.height()
        #
        # text = index.data(Qt.UserRole + 1)  # get the items text
        # item = index.data(Qt.UserRole)
        #
        # if item.isEnabled():
        #     i = qta.icon('fa.circle')
        #     i = i.pixmap(QSize(48, 48))
        #
        #     m = max([i.width(), i.height()])
        #     f = (height - 2 * self.padding) / m  # scalingfactor
        #     i = i.scaled(int(i.width() * f), int(
        #         i.height() * f))  # scale all pixmaps to the same size depending on lineheight
        #     painter.drawPixmap(QPoint(x, y + self.padding), i)
        #     x += height
        #
        # painter.drawText(QRect(x + self.padding, y + self.padding,
        #                               width - x - 2 * self.padding,
        #                               height - 2 * self.padding),
        #                  Qt.AlignLeft, text)
