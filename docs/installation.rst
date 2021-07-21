.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

.. highlight:: console

.. _specviz-installation:

Installation
============

As a Python package, SpecViz is installable via any approach that is available
for installing Python packages.  In practice the easiest way is often using the
the `Anaconda <https://anaconda.org>`__ package manager, but several other
options are available.  These are detailed below.

.. note::

    SpecViz requires Python 3.6 or later.

Install via Anaconda
--------------------

If you do not have Anaconda, please follow the `instructions here
<https://www.anaconda.com/distribution/>`_ to install it, or scroll down for
manual installation of SpecViz.

To check if Anaconda is installed correctly run the following command on a
new terminal::

    $ conda info

You should see information about your current conda installation printed out.

Creating a new conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since SpecViz uses Python 3.6 or later you may need to create a new environment with
this requirement satisfied as follows::

    $ conda create -n <environment_name> python=3.6

Installing
^^^^^^^^^^

If you are using the Space Telescope Science Institute's
`AstroConda <https://astroconda.readthedocs.io/>`_ channel,  then type the following
at any Bash terminal prompt::

    $ conda install specviz

If you do not have AstroConda installed, you can still install SpecViz from
AstrocConda by specifying the <channel> in the below install command::

    $ conda install --channel http://ssb.stsci.edu/astroconda specviz

At this point, you're done! You can launch SpecViz by typing the following at
any terminal::

    $ specviz


Uninstalling
^^^^^^^^^^^^

To uninstall via Anaconda, type the following at a command line::

    $ conda uninstall specviz


Install via source
------------------

SpecViz can also be installed manually using the source code following the
instructions below. The dependencies are listed in the ``setup.cfg`` file, and
therefore most of them will be handled automatically by the setup functions,
the exception to this is  the exception of PyQt, which may require manual
installation.

PyQt bindings
^^^^^^^^^^^^^

.. note::

    SpecViz requires PyQt for its graphical user interface. Before you install
    via source please make sure your environment includes PyQt. If you don't have
    PyQt installed, please follow the instructions in this section.

You can check if PyQt is installed by looking for it in the list of packages in your
environment. To get a list of packages you can run::

        $ pip list

If you have anaconda installed you can check via::

        $ conda list

If QtPy (not to be confused with PyQt) does not appear in the list, you must manually
install it.

Currently, only python environments with 3.6 or higher
installed can use ``pip`` to install PyQt5, in which case simply type::

    $ pip install pyqt5

to install it on your system.

In any other case, PyQt can be installed via anaconda::

    $ conda install pyqt


By cloning
^^^^^^^^^^

You may also install by cloning the repository directly

::

    $ git clone https://github.com/spacetelescope/specviz.git
    $ cd specviz
    $ git checkout tags/v0.3.0
    $ python setup.py install


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
