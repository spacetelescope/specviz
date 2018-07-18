import sys
import logging

from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.QtCore import Qt, QObject, Signal

from .widgets.main_window import MainWindow


class Application(QApplication):
    """
    Primary application object for specviz.
    """
    current_window_changed = Signal(QMainWindow)

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        # Cache a reference to the currently active window
        self._current_window = None

    def add_workspace(self):
        """
        Create a new main window instance with a new workspace embedded within.
        """
        # Initialize with a single main window
        main_window = MainWindow()
        main_window.show()

        # Connect the window focus event to the current workspace reference
        main_window.window_activated.connect(self._on_window_activated)

        self._current_window = main_window

    def remove_workspace(self):
        pass

    @property
    def current_window(self):
        """
        Returns the active current window.
        """
        return self._current_window

    def _on_window_activated(self, window):
        self._current_window = window
        self.current_window_changed.emit(self._current_window)

        logging.info("Setting active workspace to '%s'", window.workspace.name)


def start():
    # Start the application
    app = Application(sys.argv)
    app.add_workspace()

    # Enable hidpi icons
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
