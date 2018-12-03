.. highlight:: console

.. _specviz-installation:

Installation
============

As a Python package, SpecViz is installable via any approach that is available
for installing Python packages.  In practice the easiest way is often using the
the `Anaconda <https://anaconda.org>`__ package manager, but several other
options are available.  These are detailed below

distributed through the `Anaconda <https://anaconda.org>`__ package
manager. Specifically, it lives within Space Telescope Science Institute's
`AstroConda <https://astroconda.readthedocs.io/>`_ channel.



Install via Anaconda
--------------------

If you do not have Anaconda, please follow the `instructions here
<https://www.continuum.io/downloads>`_ to install it, or scroll down for
manual installation of SpecViz.


If you are using the Space Telescope Science Institute's
`AstroConda <https://astroconda.readthedocs.io/>`_ channel,  then all you have
to do to install SpecViz is simply type the following at any Bash terminal
prompt::

    $ conda install specviz

If you do not have AstroConda installed, you can still install SpecViz from
AstrocConda by specifying the channel in your install command::

    $ conda install --channel http://ssb.stsci.edu/astroconda specviz

At this point, you're done! You can launch SpecViz by typing the following at
any terminal::

    $ specviz


Uninstalling
^^^^^^^^^^^^

To uninstall via Anaconda, simply type the following at a command line::

    $ conda uninstall specviz


Install via source
------------------

SpecViz can also be installed manually using the source code followint the
instructions below. The dependencies are listed in the ``setup.cfg`` file, and
therefore most of them will be handled automatically by the setup functions,
the exception to this is  the exception of PyQt, which may require manual
installation.


By using ``pip``
^^^^^^^^^^^^^^^^

Clone the SpecViz repository somewhere on your system, and install locally using
``pip``. If you are using an Anaconda virtual environment, please be sure to
activate it first before installing: ``$ source activate <environment_name>``.

::

    $ pip install git+http://github.com/spacetelescope/specviz.git@v0.4.4

This uses the ``pip`` installation system, so please note that

1. You need to have ``pip`` installed (included in most Python installations).
2. You do **not** need to run ``python setup.py install``.
3. You do **not** need to install the dependencies by hand (except for PyQt).

Likewise, the ``pip`` command will use your default Python to install.
You can specify by using ``pip2`` or ``pip3``, if you're not using a virtual
environment.


By cloning
^^^^^^^^^^

You may also install by cloning the repository directly

::

    $ git clone https://github.com/spacetelescope/specviz.git
    $ cd specviz
    $ git checkout tags/v0.3.0
    $ python setup.py install


PyQt bindings
^^^^^^^^^^^^^

SpecViz requires PyQt. Currently, only python environments with 3.5 or higher
installed can use ``pip`` to install PyQt5, in which case simply type::

    $ pip install pyqt5

to install it on your system.

In any other case, PyQt can be installed via anaconda::

    $ conda install pyqt


Uninstalling
^^^^^^^^^^^^

To uninstall via ``pip``, simply type the following at a command line::

    $ pip uninstall specviz


Known Issues
------------

On a Mac with Qt5, depending on exactly how you have set up Anaconda, you might
see the following error after following the above instructions::

    This application failed to start because it could not find or load the Qt platform plugin "cocoa".

    Reinstalling the application may fix this problem.

If you see this message, you have encountered an incompatibility between
Anaconda's packaging of Qt4 and Qt5. The workaround is to uninstall Qt4 with the
following command::

    $ conda uninstall pyqt qt

and SpecViz should now happily run.

Conversely, if you've had PyQt5 installed previously and you wish to run the
PyQt4 version, you may run into a similar error::

    $ RuntimeError: the PyQt4.QtCore and PyQt5.QtCore modules both wrap the
    QObject class

This issue can be solved with the following command::

    $ conda uninstall pyqt5 qt5
