.. _doc_launching:

Launching SpecViz
=================

Once you've installed SpecViz, you can launch it via the command line::

    $ specviz


If you only wish to inspect a single FITS or ASCII file using the default
:ref:`doc_custom_loaders` file formatting, you can also pass in the filename
as a command line argument, as follows::

    $ specviz filename


You may also include the name of a custom loader as second optional argument::

    $ specviz filename --format="my-custom-format"