import importlib
import logging
import os
import pkgutil
import sys, inspect

import click
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMainWindow

from . import plugins
from .core.plugin import Plugin
from .utils import DATA_PATH
from .widgets.workspace import Workspace


class Application(QApplication):
    """
    Primary application object for specviz.
    """
    current_workspace_changed = Signal(QMainWindow)
    workspace_added = Signal(Workspace)

    def __init__(self, *args, file_path=None, file_loader=None, embeded=False,
                 **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        # Cache a reference to the currently active window
        self._current_workspace = self.add_workspace()

        # Set embed mode state
        self.current_workspace.set_embeded(embeded)

        # If a file path has been given, automatically add data
        if file_path is not None:
            self.current_workspace.load_data(
                file_path, file_loader, display=True)

        # Load local plugins
        self.load_local_plugins()

    def add_workspace(self):
        """
        Create a new main window instance with a new workspace embedded within.
        """
        # Initialize with a single main window
        workspace = Workspace()
        workspace.show()

        # Connect the window focus event to the current workspace reference
        workspace.window_activated.connect(self._on_window_activated)

        return workspace

    def load_local_plugins(self, filt=None):
        # Load plugins
        def iter_namespace(ns_pkg):
            # Specifying the second argument (prefix) to iter_modules makes the
            # returned name an absolute name instead of a relative one. This
            # allows import_module to work without having to do additional
            # modification to the name.
            return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")

        # Import plugins modules into current namespace
        loaded_plugins = {name: importlib.import_module(name)
                          for finder, name, ispkg
                          in iter_namespace(plugins)}

        # Instantiate plugins to include them in the UI
        for sub_cls in Plugin.__subclasses__():
            logging.info("Loading plugin '{}'.".format(sub_cls.__name__))
            sub_cls(filt=filt)

    def remove_workspace(self):
        pass

    @property
    def current_workspace(self):
        """
        Returns the active current window.
        """
        return self._current_workspace

    @current_workspace.setter
    def current_workspace(self, value):
        self._current_workspace = value
        self.current_workspace_changed.emit(self.current_workspace)

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

    import qdarkstyle
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    # Set application icon
    app.setWindowIcon(QIcon(os.path.join(DATA_PATH, "icon.png")))


    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
