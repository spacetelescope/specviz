import sys

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt

from .client import launch as client_launch
from .widgets.main_window import MainWindow
from .core.hub import Hub


def start(server_ip=None, client_ip=None):
    # Start the application
    app = QApplication(sys.argv)

    # Add a hub object to this application. Attaching it here means
    # we can have a central hub for every application instance.
    app.hub = Hub()

    # Enable hidpi icons
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
