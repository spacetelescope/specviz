# Licensed under a 3-clause BSD style license - see LICENSE.rst

try:
    from specviz.version import version as __version__
except Exception:
    # package is not installed
    __version__ = "unknown"

__all__ = ['__version__']

print('specviz is no longer supported, please use jdaviz. '
      'If you must use legacy specviz, please try v0.7.1 '
      'in Python 3.6.')
