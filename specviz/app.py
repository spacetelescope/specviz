"""SpecViz front-end GUI access point.
This script will start the GUI.

"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# STDLIB
import signal
import sys
import warnings
import os
import logging

# THIRD-PARTY
from astropy.utils.exceptions import AstropyUserWarning

# LOCAL
from qtpy.QtWidgets import QApplication
from qtpy.QtGui import QIcon
from qtpy.QtCore import QTimer
from .ui.viewer import Viewer
from .ui.widgets.utils import ICON_PATH
from .core.comms import dispatch, DispatchHandle


class App(object):
    def __init__(self, argv):
        super(App, self).__init__()
        self.viewer = Viewer()

        if len(argv) > 1:
            file_name = argv[1]

            for arg in argv:
                if '--format=' in arg:
                    file_filter = arg.strip("--format=")
                    break
            else:
                file_filter = "Auto (*)"

            dispatch.on_file_read.emit(file_name, file_filter=file_filter)

def setup():
    qapp = QApplication(sys.argv)
    # qapp.setGraphicsSystem('native')
    qapp.setWindowIcon(QIcon(os.path.join(ICON_PATH, 'application',
                                          'icon.png')))

    #http://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    app = App(sys.argv)
    app.viewer.main_window.show()

    return qapp, app


def embed():
    """
    Used when launching the application within a shell, and the application
    namespace is still needed.
    """
    qapp, app = setup()
    qapp.exec_()

    return app


def main():
    """
    Used when launching the application as standalone.
    """
    signal.signal(signal.SIGINT, sigint_handler)
    qapp, app = setup()
    sys.exit(qapp.exec_())


def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    warnings.warn('KeyboardInterrupt caught; specviz will terminate',
                  AstropyUserWarning)
    QApplication.quit()


def glue_setup():

    try:
        import glue  # noqa
    except ImportError:
        logging.warning("Failed to import SpecVizViewer; Glue installation not found.")
        return

    # Check that the version of glue is recent enough
    from distutils.version import LooseVersion
    from glue import __version__
    if LooseVersion(__version__) < LooseVersion('0.10.2'):
        raise Exception("glue 0.10.2 or later is required for the specviz plugin")

    from .external.glue.data_viewer import SpecVizViewer
    from glue.config import qt_client
    qt_client.add(SpecVizViewer)


if __name__ == '__main__':
    main()
