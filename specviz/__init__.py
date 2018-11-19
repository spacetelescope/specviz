# Licensed under a 3-clause BSD style license - see LICENSE.rst

# Packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# Enforce Python version check during package import.
# This is the same check as the one at the top of setup.py
import os
import sys
import logging

__minimum_python_version__ = "3.5"

class UnsupportedPythonError(Exception):
    pass

if sys.version_info < tuple((int(val) for val in __minimum_python_version__.split('.'))):
    raise UnsupportedPythonError("specviz does not support Python < {}".format(__minimum_python_version__))

if not _ASTROPY_SETUP_:

    import pyqtgraph as pg
    from configparser import ConfigParser

    # Setup logging level and display
    logging.basicConfig(format='specviz [%(levelname)-8s]: %(message)s',
                        level=logging.INFO)

    def load_settings():
        # Get the path relative to the user's home directory
        path = os.path.expanduser("~/.specviz")

        # If the directory doesn't exist, create it
        if not os.path.exists(path):
            os.mkdir(path)

        # Parse user settings
        parser = ConfigParser()
        parser['PyQtGraph'] = {}

        # Check if there already exists a pyqtgraph settings file
        user_settings_path = os.path.join(path, "user_settings.ini")

        if os.path.exists(user_settings_path):
            parser.read(user_settings_path)

        pyqtgraph_settings = {
            'leftButtonPan': parser['PyQtGraph'].getboolean('leftbuttonpan', True),
            'foreground': parser['PyQtGraph'].get('foreground', 'k'),
            'background': parser['PyQtGraph'].get('background', 'w'),
            'antialias': parser['PyQtGraph'].getboolean('antialias', False),
            'imageAxisOrder': parser['PyQtGraph'].get('imageaxisorder', 'col-major'),
            'useWeave': parser['PyQtGraph'].getboolean('useweave', False),
            'weaveDebug': parser['PyQtGraph'].getboolean('weavedebug', False),
            'useOpenGL': parser['PyQtGraph'].getboolean('useopengl', False),
        }

        if not os.path.exists(user_settings_path):
            parser['PyQtGraph'] = pyqtgraph_settings

            with open(user_settings_path, 'w') as config_file:
                parser.write(config_file)

        # Set the pyqtgraph options
        pg.setConfigOptions(**pyqtgraph_settings)

    load_settings()
