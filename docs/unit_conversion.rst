.. _specviz-unit-conversion:

.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

Unit Conversion
===============

How Unit Conversion Works
-------------------------

SpecViz allows the user to change the units on their spectra.
It uses the `astropy.units <http://docs.astropy.org/en/stable/units/>`_
module for unit conversion.

To change the units, click on the blue “Change Units” button in the :ref:`plot toolbar <specviz-plot-toolbar>`.
A dialog box will appear and you can change the X or Y axis units by selecting new units
from one of the two drop down boxes. The boxes are populated by potential compatible units.
The user can then select any of those options - as well as a "Custom" option - and the changes
will be reflected in the plot.

.. image:: _static/specviz_uc_custom1.png

If you do not see the units you want in the drop down, you can select the “Custom” option.
This will then make visible a text box where you can enter your chosen units. To the left
of the text box, a label will let you know if you are entering valid
`astropy unit <http://docs.astropy.org/en/stable/units/index.html#>`_. Red coloring means
the units are invalid, and there should be suggestions provided. Green coloring means you
entered valid units and can now press the “OK” button. If the units are incompatible,
the current plot units will not be changed.

Invalid custom unit:

.. image:: _static/specviz_uc_custom2.png

Valid custom `astropy unit <http://docs.astropy.org/en/stable/units/index.html#>`_:

.. image:: _static/specviz_uc_custom3.png
