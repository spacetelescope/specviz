import importlib
import logging
import os
import pkgutil
import sys, inspect

import click
from qtpy.QtCore import Qt, Signal
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMainWindow

from . import plugins, __version__
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
                 dev=False, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        # If specviz is not being embded in another application, go ahead and
        # perform the normal gui setup procedure.
        if not embeded:
            # Cache a reference to the currently active window
            self.current_workspace = self.add_workspace()

            # Add an initially empty plot
            self.current_workspace.add_plot_window()

            # Set embed mode state
            self.current_workspace.set_embeded(embeded)

            # Load local plugins
            self.load_local_plugins()

        if dev:
            from astropy.modeling.models import Gaussian1D
            import numpy as np
            from specutils import Spectrum1D
            import astropy.units as u

            y = Gaussian1D(mean=50, stddev=10)(np.arange(100)) + np.random.sample(100) * 0.1

            spec1 = Spectrum1D(flux=y * u.Jy,
                            spectral_axis=np.arange(100) * u.AA)
            spec2 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                            spectral_axis=np.arange(100) * u.Hz)
            spec3 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                            spectral_axis=np.arange(100) * u.Hz)

            # data_item = DataItem("My Data 1", identifier=uuid.uuid4(), data=spec1)
            # data_item2 = DataItem("My Data 2", identifier=uuid.uuid4(), data=spec2)
            # data_item3 = DataItem("My Data 3", identifier=uuid.uuid4(), data=spec3)

            self.current_workspace.model.add_data(spec1, "Spectrum 1")
            self.current_workspace.model.add_data(spec2, "Spectrum 2")
            self.current_workspace.model.add_data(spec3, "Spectrum 3")

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

        return workspace

    @staticmethod
    def load_local_plugins(application=None, filt=None):
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
        self.current_workspace = window
        self.current_workspace_changed.emit(self.current_workspace)

        logging.info("Setting active workspace to '%s'", window.name)


@click.command()
@click.option('--file_path', '-F', type=click.Path(exists=True), help="Load the file at the given path on startup.")
@click.option('--loader', '-L', type=str, help="Use specified loader when opening the provided file.")
@click.option('--embed', '-E', is_flag=True, help="Only display a single plot window. Useful when embedding in other applications.")
@click.option('--dev', '-D', is_flag=True, help="Open SpecViz in developer mode. This mode auto-loads example spectral data.")
@click.option('--version', '-V', is_flag=True, help="Print version information", is_eager=True)
def start(version=False, file_path=None, loader=None, embed=None, dev=None):
    if version:
        print(__version__)
        return

    # Start the application, passing in arguments
    app = Application(sys.argv, file_path=file_path, file_loader=loader,
                      embeded=embed, dev=dev)

    # Enable hidpi icons
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Set application icon
    app.setWindowIcon(QIcon(os.path.join(DATA_PATH, "icon.png")))

    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
