# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This is an Astropy affiliated package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

if not _ASTROPY_SETUP_:
    # For egg_info test builds to pass, put package imports here.

    pass

# Setup a temporary global settings singleton-esque object
GLOBAL_SETTINGS = {}

from .interfaces.loaders import _load_yaml, _load_py

_load_yaml()
_load_py()

# cache the line lists for speedier access
from .core import linelist
linelist.populate_linelists_cache()

from .plugins import *
