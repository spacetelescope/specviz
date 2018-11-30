import importlib
import logging
import os
import pkgutil
import random
import sys

import astropy.units as u
import click
import numpy as np
from astropy.modeling.models import Gaussian1D
from qtpy.QtCore import QTimer, Qt, Signal
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QDialog, QMainWindow
from qtpy.uic import loadUi
from specutils import Spectrum1D

from . import __version__, plugins
from .widgets.workspace import Workspace


class Application(QApplication):
    """
    Primary application object for specviz.
    """
    current_workspace_changed = Signal(QMainWindow)
    workspace_added = Signal(Workspace)

    def __init__(self, *args, file_path=None, file_loader=None, embedded=False,
                 dev=False, skip_splash=False, **kwargs):
        super(Application, self).__init__(*args, **kwargs)

        # Set application icon
        self.setWindowIcon(QIcon(":/icons/specviz.icns"))

        # Load local plugins
        self.load_local_plugins()

        # cache the line lists for speedier access
        from .core import linelist
        linelist.populate_linelists_cache()

        # Show splash
        if not skip_splash:
            self._splash_dialog = SplashDialog(2000)
            self._splash_dialog.exec()

        # If specviz is not being embded in another application, go ahead and
        # perform the normal gui setup procedure.
        if not embedded:
            # Cache a reference to the currently active window
            self.current_workspace = self.add_workspace()

            # Add an initially empty plot
            self.current_workspace.add_plot_window()

            # Set embed mode state
            self.current_workspace.set_embedded(embedded)

        if dev:
            y = Gaussian1D(mean=50, stddev=10)(np.arange(100)) + np.random.sample(100) * 0.1

            spec1 = Spectrum1D(flux=y * u.Jy,
                            spectral_axis=np.arange(100) * u.AA)
            spec2 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                            spectral_axis=np.arange(100) * u.Hz)
            spec3 = Spectrum1D(flux=np.random.sample(100) * u.erg,
                            spectral_axis=np.arange(100) * u.Hz)

            data_item = self.current_workspace.model.add_data(spec1, "Spectrum 1")
            self.current_workspace.model.add_data(spec2, "Spectrum 2")
            self.current_workspace.model.add_data(spec3, "Spectrum 3")

            # Set the first item as selected
            self.current_workspace.force_plot(data_item)

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


class SplashDialog(QDialog):
    def __init__(self, wait_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wait_time = wait_time
        self._total_time = 0

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAutoFillBackground(True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "widgets", "ui", "splash_non_modal.ui")),
            self)

        # Set the version number
        self.version_label.setText("Version {}".format(__version__))

        self._timer = QTimer()
        self._timer.timeout.connect(self.calculate_progress)
        self._timer.start(300)

    def calculate_progress(self):
        rand = random.randrange(100, 500)
        self._total_time += rand
        self.progress_bar.setValue(self._total_time/self._wait_time*100)

        if self._total_time > self._wait_time:
            self._timer.stop()
            self.close()


@click.command()
@click.option('--hide_splash', '-H', is_flag=True, help="Hide the startup splash screen.")
@click.option('--file_path', '-F', type=click.Path(exists=True), help="Load the file at the given path on startup.")
@click.option('--loader', '-L', type=str, help="Use specified loader when opening the provided file.")
@click.option('--embed', '-E', is_flag=True, help="Only display a single plot window. Useful when embedding in other applications.")
@click.option('--dev', '-D', is_flag=True, help="Open SpecViz in developer mode. This mode auto-loads example spectral data.")
@click.option('--version', '-V', is_flag=True, help="Print version information", is_eager=True)
def start(version=False, file_path=None, loader=None, embed=None, dev=None, hide_splash=False):
    if version:
        print(__version__)
        return

    # Start the application, passing in arguments
    app = Application(sys.argv, file_path=file_path, file_loader=loader,
                      embedded=embed, dev=dev, skip_splash=hide_splash)

    # Enable hidpi icons
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    sys.exit(app.exec_())


if __name__ == '__main__':
    start()
