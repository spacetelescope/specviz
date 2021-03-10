.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

.. highlight:: console

.. _specviz-launching:

Launching SpecViz
=================

Once the user has installed SpecViz, they can launch it via the command line::

    $ specviz

If the user wishes to inspect a single file, they can also pass in the filename
as a command line argument along with the ``-F`` flag as follows::

    $ specviz -F <filename>

.. code-block::bash

    $ specviz -F ~/Downloads/COS_FUV.fits

You can get further help with the command line options by simply typing
``specviz --help``.

Specifying Loaders
^^^^^^^^^^^^^^^^^^

SpecViz uses :ref:`data loaders <specviz_loading_data>` to open spectra files.
In the above case, the loader registry functionality will attempt to select
the best available loader for the data. If the user wishes to specify a
specific loader for their data, a ``-L`` flag can be passed with the loader
name::

    $ specviz -F <filename> -L <loader_name>

.. code-block::bash

    $ specviz -F ~/Downloads/COS_FUV.fits -L HST/COS

For example you can load your APOGEE spectrum file using the ``APOGEE apStar`` loader
as follows::

    $ specviz -F ~/data/apStar-r5-2M27333842+4223549.fits  -L APOGEE\ apStar

To get a list of loaders please see the :ref:`table of loaders <specviz-loader-list>`
in the Loading Data section.


