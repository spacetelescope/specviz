from glue.viewers.common.viewer import BaseViewer
from glue.viewers.common.qt.base_widget import BaseQtViewerWidget

from ...widgets.main_window import MainWindow

__all__ = ['SpecvizViewer']


class SpecvizViewer(BaseViewer, BaseQtViewerWidget):

    # Note that we inherit from BaseViewer and BaseQtViewerWidget since we
    # don't want any of the layer artist/state infrastructure normally used
    # for data viewers.

    LABEL = 'Specviz'

    def __init__(self, session, parent=None):
        """
        :type session: :class:`~glue.core.Session`
        """

        BaseQtViewerWidget.__init__(self, parent)
        BaseViewer.__init__(self, session)

        # Add the main Specviz widget
        self.specviz_window = MainWindow()
        self.setCentralWidget(self.specviz_window)
