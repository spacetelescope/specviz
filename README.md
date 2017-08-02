# SpecViz
[![astropy](http://img.shields.io/badge/powered%20by-AstroPy-orange.svg?style=flat)](http://www.astropy.org/) [![Build Status](https://travis-ci.org/spacetelescope/specviz.svg?branch=loaders)](https://travis-ci.org/spacetelescope/specviz) [![Documentation Status](http://readthedocs.org/projects/specviz/badge/?version=latest)](http://specviz.readthedocs.io/en/latest/?badge=latest)

An gui-based interactive analysis tool for one dimensional astronomical data
using Python.

For installation instructions, please visit the
[online documentation](https://specviz.readthedocs.io/).
All documentation can also be found in the `docs` directory of the source.

## Install

SpecViz can also be installed manually using the source code and requires the
following dependencies to be installed on your system. Most of these will be
handled automatically by the setup functions, with the exception of PyQt/PySide.

* Python 3 (recommended) or Python 2
* PyQt5 (recommended), PyQt4, or PySide
* Astropy
* Numpy
* Scipy
* PyQtGraph
* qtpy


### By using `pip`

Clone the SpecViz repository somewhere on your system, and install locally using
`pip`. If you are using an Anaconda virtual environment, please be sure to
activate it first before installing: `$ source activate <environment_name>`.

```
$ pip install git+http://github.com/spacetelescope/specviz.git@v0.4.0
```

This uses the `pip` installation system, so please note that

1. You need to have `pip` installed (included in most Python installations).
2. You do **not** need to run `python setup.py install`.
3. You do **not** need to install the dependencies by hand (except for PyQt).

Likewise, the `pip` command will use your default Python to install.
You can specify by using `pip2` or `pip3`, if you're not using a virtual
environment.


### By cloning

You may also install by cloning the repository directly

```
$ git clone https://github.com/spacetelescope/specviz.git
$ cd specviz
$ git checkout tags/v0.3.0
$ python setup.py install
```

## Contributing

To contribute code to the repository, please *fork* the repo first and then issue a pull request with your changes.

## Support

Please submit questions and comments to the [forum](https://groups.google.com/forum/#!forum/specviz)
directly, or through the user mailing list at specviz@googlegroups.com. If you
have found a bug, feel free to [open an issue](https://github.com/spacetelescope/specviz/issues).
