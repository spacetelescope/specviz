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


In the above case, the loader registry functionality will attempt to select
the best available loader for the data. If the user wishes to specify a
specific loader for their data, a ``-L`` flag can be passed with the loader
name

    $ specviz -F <filename> -L <loader_name>

.. code-block::bash

    $ specviz -F ~/Downloads/COS_FUV.fits -L HST/COS

To get further help with the command line options, simply type
``specviz --help``.
