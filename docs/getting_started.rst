.. _specviz-start:

Getting Started
===============

Loading a Basic Spectrum
------------------------

Lets start by loading a test spectrum. If you followed the steps in
:ref:`specviz-launching`, you should see the specviz window up, but without a
spectrum.

There are two options to load a spectrum:

1. Load the spectrum with a pre-defined data loader, or a custom user-defined data loader.
2. Utilize the :doc:`Loader Wizard </loader_wizard>` to create a new custom loader, and use that to load your data.

Either way, the specific loader for your data can be selected from the drop
down list in the open file dialog

.. image:: _static/open_file_dialog.png

.. image:: _static/loader_select.png

Once the file has been loaded, the spectrum should plot.


Exporting Spectra
-----------------

A user can export a given spectrum in the data list by highlighting the
spectrum and clicking the ``Export Data`` button in the main toolbar. This
will provide the user with a save file dialog where they may choose where to
save the exported spectrum.

.. note::

    `ECSV <http://docs.astropy.org/en/stable/api/astropy.io.ascii.Ecsv.html>`_
    is currently the only supported export format. This will change in the
    future as more exporting formats are supported in the specutils package.

