#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from setuptools import setup
setup(use_scm_version={'write_to': os.path.join('specviz', 'version.py')})
