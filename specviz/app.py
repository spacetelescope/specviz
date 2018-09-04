import logging
import sys

import click
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import QApplication, QMainWindow

from .widgets.workspace import Workspace
import pkgutil
import importlib

import specviz.plugins


class Application(QApplication):
    """
    Primary application object for specviz.
    """
    current_workspace_changed = Signal(QMainWindow)

    def __init__(self, *args, file_path=None, file_loader=None, embeded=False, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        # Cache a reference to the currently active window
        self._current_workspace = None

        # Create a default workspace
        self.add_workspace()

        # Set embed mode state
        self.current_workspace.set_embeded(embeded)

        # If a file path has been given, automatically add data
        if file_path is not None:
            self.current_workspace.load_data(
                file_path, file_loader, display=True)

    def add_workspace(self):
        """
        Create a new main window instance with a new workspace embedded within.
        """
        # Initialize with a single main window
        workspace = Workspace()
        workspace.show()

        # Connect the window focus event to the current workspace reference
        workspace.window_activated.connect(self._on_window_activated)

        self._current_workspace = workspace

        from .plugins.statistics.main import Statistics
        from .plugins.model_editor.main import ModelEditor
        from .plugins.smoothing.main import SmoothingDialog

        Statistics()
        ModelEditor()
        SmoothingDialog()

        # Load plugins
        def iter_namespace(ns_pkg):
            # Specifying the second argument (prefix) to iter_modules makes the
            # returned name an absolute name instead of a relative one. This allows
            # import_module to work without having to do additional modification to
            # the name.
            return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

        myapp_plugins = {
            name: importlib.import_module(name)
            for finder, name, ispkg
            in iter_namespace(specviz.plugins)
        }

        print(myapp_plugins)

    def remove_workspace(self):
        pass

    @property
    def current_workspace(self):
        """
        Returns the active current window.
        """
        return self._current_workspace

    def _on_window_activated(self, window):
        self._current_workspace = window
        self.current_workspace_changed.emit(self.current_workspace)

        logging.info("Setting active workspace to '%s'", window.name)


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

    # import qdarkstyle
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())


    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
