"""
Registry library
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import yaml
import os, sys
import importlib
import logging

import astropy.io.registry as io_registry

#-- local
from ..core.data import Spectrum1DRef
from ..core.linelist import LineList
from ..io.yaml_loader import FitsYamlRegister, EcsvYamlRegister, AsciiYamlRegister, LineListYamlRegister

from ..io.loaders import *


def load_yaml_reader(f_path):
    with open(f_path, 'r') as f:
        custom_loader = yaml.load(f)
        custom_loader.set_filter()

    if any(ext in custom_loader.extension for ext in ['fits']):
        loader = FitsYamlRegister(custom_loader)

    elif any(ext in custom_loader.extension for ext in ['list']):
        loader = LineListYamlRegister(custom_loader)

    elif any(ext in custom_loader.extension for ext in ['ecsv']):
        loader = EcsvYamlRegister(custom_loader)

    elif any(ext in custom_loader.extension for ext in ['txt', 'dat']):
        loader = AsciiYamlRegister(custom_loader)

    try:
        if 'list' in custom_loader.extension:
            io_registry.register_reader(custom_loader.filter,
                                        LineList,
                                        loader.reader)
        else:
            io_registry.register_reader(custom_loader.filter,
                                        Spectrum1DRef,
                                        loader.reader)
            io_registry.register_identifier(custom_loader.filter,
                                            Spectrum1DRef,
                                            loader.identify)
    except io_registry.IORegistryError as e:
        logging.error(e)

    return custom_loader.filter


def _load_py():
    """ Loads built-in and custom python loaders

    Loaders from the io.loaders module will be included from the
    import statement.
    Python modules (.py ending) found in the following locations will be
    auto-loaded into the registry for data loading.

    1. .specviz folder in the user's HOME directory

    """

    usr_path = os.path.join(os.path.expanduser('~'), '.specviz')

    # This order determines priority in case of duplicates; paths higher
    # in this list take precedence
    #
    # Leaving in list format incase other locations want to be added
    # in the future
    check_paths = [usr_path]

    if not os.path.exists(usr_path):
        os.mkdir(usr_path)

    for path in check_paths:
        for mod in [x for x in os.listdir(path) if x.endswith('.py')]:
            mod = mod.split('.')[0]
            sys.path.insert(0, path)

            try:
                mod = importlib.import_module(mod)
                sys.path.pop(0)
            except ImportError:
                logging.warning("Unable to import {} in {}.".format(mod, path))

            # for _, func in members:
            #     if hasattr(func, 'loader_wrapper') and func.loader_wrapper:
            #         self._members.append(func)

def _load_yaml():
    """ Loads yaml files as custom loaders.

    YAML files found in the following three locations will be auto-loaded
    into the registry for data loading.

    1. .specviz folder in the user's HOME directory
    2. the current working directory
    3. the linelists directory delivered with this package.

    The io_registry will be updated with the YAML schematics for each of the
    different filetypes.  Errors in loading the registry will write an error
    to the log.

    """
    cur_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            '..', 'data', 'yaml_loaders'))
    usr_path = os.path.abspath(os.path.join(os.path.expanduser('~'),
                                            '.specviz'))
    lines_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                              'linelists')

    # This order determines priority in case of duplicates; paths higher
    # in this list take precedence
    check_paths = [usr_path, cur_path, lines_path]

    if not os.path.exists(usr_path):
        os.mkdir(usr_path)

    for path in check_paths:
        for file_name in [x for x in os.listdir(path)
                          if x.endswith('yaml')]:
            f_path = os.path.join(path, file_name)
            load_yaml_reader(f_path)


class YAMLLoader(yaml.YAMLObject):
    """ Helper to load YAML files
    """
    yaml_tag = u'!CustomLoader'

    def __init__(self, extension, name, data, dispersion, uncertainty, mask,
                 wcs, meta):
        self.name = name
        self.extension = extension
        self.data = data
        self.dispersion = dispersion
        self.uncertainty = uncertainty
        self.mask = mask
        self.wcs = wcs
        self.meta = meta or {}
        self.filter = None

    def set_filter(self):
        if not isinstance(self.extension, list):
            self.extension = [self.extension]

        filter_string = ' '.join(['*.{}'.format(x)
                                   for x in self.extension])

        if "fits" in self.extension:
            filter_string += " *fits.gz"

        self.filter = "{} ({})".format(self.name, filter_string)