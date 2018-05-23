import sys

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Qt

from .widgets.main_window import MainWindow
from .core.hub import Hub


def start():
    # Start the application
    app = QApplication(sys.argv)

    # Enable hidpi icons
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
