"""SpecViz is a tool for 1-D spectral visualization and analysis of
astronomical data.

Usage:
  specviz
  specviz load <path> [--loader=<name>]
  specviz config <path>
  specviz (-h | --help)
  specviz --version

Options:
  -h --help             Show this screen.
  --version             Show version.
  --loader=<name>       Custom loader for data set. Can also be a path.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import os
import signal
import sys
import warnings

from astropy.utils.exceptions import AstropyUserWarning
from qtpy.QtCore import QTimer, Qt
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QApplication, QMenu, QToolBar
from docopt import docopt

from . import GLOBAL_SETTINGS
from .widgets.utils import ICON_PATH
from .core.events import dispatch
from .widgets.windows import MainWindow

try:
    from .version import version
except ModuleNotFoundError:
    version = None
    logging.error("Version cannot be imported until package is installed.")


class App(object):
    def __init__(self, hidden=None, disabled=None, menubar=True):
        hidden = hidden or {}
        disabled = disabled or {}

        self._instanced_plugins = {}

        # Instantiate main window object
        self._all_tool_bars = {}

        self.main_window = MainWindow(menubar=menubar)
        if self.main_window.menu_bar is not None:
            self.menu_docks = self.main_window.menu_bar.addMenu('Plugins')
            self.menu_docks.addSeparator()
        else:
            self.menu_docks = None

        # self.main_window.setDockNestingEnabled(True)

        # Load system and user plugins
        self.load_plugins(hidden=hidden, disabled=disabled)

        # Setup up top-level connections
        self._setup_connections()

        # Parse arguments
        try:
            args = docopt(__doc__, version=version)
        except SystemExit:
            logging.error("Received unknown command line arguments.")
        else:
            self._parse_args(args)

    def _parse_args(self, args):
        if args.get("load", False):
            file_filter = args.get("--loader", "Auto (*)")
            dispatch.on_file_read.emit(args.get("<path>"),
                                       file_filter=file_filter)

    def load_plugins(self, hidden=None, disabled=None):
        from .interfaces.registries import plugin_registry

        self._instanced_plugins = {
            x.name:x() for x in plugin_registry.members
            if not disabled.get(x.name, False)}

        for inst_plgn in sorted(self._instanced_plugins.values(),
                                      key=lambda x: x.priority):
            if inst_plgn.location != 'hidden':
                if inst_plgn.location == 'right':
                    location = Qt.RightDockWidgetArea
                elif inst_plgn.location == 'top':
                    location = Qt.TopDockWidgetArea
                else:
                    location = Qt.LeftDockWidgetArea

                self.main_window.addDockWidget(location, inst_plgn)

                if hidden.get(inst_plgn.name):
                    inst_plgn.hide()

                # Add this dock's visibility action to the menu bar
                if self.menu_docks is not None:
                    self.menu_docks.addAction(inst_plgn.toggleViewAction())

        # Sort actions based on priority
        all_actions = [y for x in self._instanced_plugins.values()
                       for y in x._actions]
        all_categories = {}

        for act in all_actions:
            if all_categories.setdefault(act['category'][0], -1) < \
                    act['priority']:
                all_categories[act['category'][0]] = act['category'][1]

        for k, v in all_categories.items():
            tool_bar = self._get_tool_bar(k, v)

            for act in sorted([x for x in all_actions
                               if x['category'][0] == k],
                              key=lambda x: x['priority'],
                              reverse=True):
                tool_bar.addAction(act['action'])

            tool_bar.addSeparator()

        # Sort tool bars based on priority
        all_tool_bars = self._all_tool_bars.values()

        for tb in sorted(all_tool_bars, key=lambda x: x['priority'],
                         reverse=True):
            self.main_window.addToolBar(tb['widget'])

    def _get_tool_bar(self, name, priority):
        if name is None:
            name = "User Plugins"
            priority = -1

        if name not in self._all_tool_bars:
            tool_bar = QToolBar(name)
            tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            tool_bar.setMovable(False)

            self._all_tool_bars[name] = dict(widget=tool_bar,
                                             priority=int(priority),
                                             name=name)
        else:
            if self._all_tool_bars[name]['priority'] == 0:
                self._all_tool_bars[name]['priority'] = priority

        return self._all_tool_bars[name]['widget']

    def _setup_connections(self):
        # Listen for subwindow selection events, update layer list on selection
        self.main_window.mdi_area.subWindowActivated.connect(
            lambda wi: dispatch.on_selected_window.emit(
            window=wi.widget() if wi is not None else None))


def setup():
    qapp = QApplication(sys.argv)
    # qapp.setGraphicsSystem('native')
    qapp.setWindowIcon(QIcon(os.path.join(ICON_PATH, 'application',
                                          'icon.png')))

    #http://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-co
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    app = App()
    app.main_window.show()

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
        logging.warning("Failed to import SpecVizViewer; Glue installation "
                        "not found.")
        return

    # Check that the version of glue is recent enough
    from distutils.version import LooseVersion
    from glue import __version__
    if LooseVersion(__version__) < LooseVersion('0.10.2'):
        raise Exception("glue 0.10.2 or later is required for the specviz "
                        "plugin")

    from .third_party.glue.data_viewer import SpecVizViewer
    from glue.config import qt_client
    qt_client.add(SpecVizViewer)


if __name__ == '__main__':
    main()
