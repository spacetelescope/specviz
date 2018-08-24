import logging
import sys

import click
from qtpy.QtCore import QObject, Qt, Signal
from qtpy.QtWidgets import QApplication, QMainWindow

from .widgets.main_window import MainWindow


class Application(QApplication):
    """
    Primary application object for specviz.
    """
    current_window_changed = Signal(QMainWindow)

    def __init__(self, *args, file_path=None, file_loader=None, embeded=False, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        # Cache a reference to the currently active window
        self._current_window = None

        # Create a default workspace
        self.add_workspace()

        # Set embed mode state
        self.current_window.set_embeded(embeded)

        # If a file path has been given, automatically add data
        if file_path is not None:
            self.current_window.workspace.load_data(
                file_path, file_loader, display=True)

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


@click.command()
@click.option('--file_path', '-F', type=click.Path(exists=True), help="Load the file at the given path on startup.")
@click.option('--loader', '-L', type=str, help="Use specified loader when opening the provided file.")
@click.option('--embed', '-E', is_flag=True, help="Only display a single plot window. Useful when embedding in other applications.")
def start(file_path=None, loader=None, embed=None):
    # Start the application, passing in arguments
    app = Application(sys.argv, file_path=file_path, file_loader=loader,
                      embeded=embed)

    # Enable hidpi icons
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
