.. highlight:: console

.. _specviz-launching:

Launching SpecViz
=================

Once the user has installed SpecViz, they can launch it via the command line::

    $ specviz


If the user wishes to inspect a single file, they can also pass in the filename
as a command line argument along with the ``-F`` flag as follows::

    $ specviz -F filename




You may also include the name of a custom loader as second optional argument::

    $ specviz filename --format="my-custom-format"
