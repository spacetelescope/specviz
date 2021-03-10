.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

Exporting Data
==============

A user can export a given spectrum in the data list by highlighting the
spectrum and clicking the ``Export Data`` button in the main toolbar. This
will provide the user with a save file dialog where they may choose where to
save the exported spectrum.

.. note::

    `ECSV <http://docs.astropy.org/en/stable/api/astropy.io.ascii.Ecsv.html>`_
    is currently the only supported export format. This will change in the
    future as more exporting formats are supported in the specutils package.
