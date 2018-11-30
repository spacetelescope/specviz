.. image:: _static/title_horizontal.png

|

Introduction
============

SpecViz is a tool for visualization and quick-look analysis of 1D astronomical
spectra. It is written in the Python programming language, and therefore can be
run anywhere Python is supported (see :ref:`specviz-installation`). It is based
on the `Astropy Specutils packgage <https://specutils.rtfd.io>`_. SpecViz is
capable of reading data from FITS and ASCII tables, and supports the creation
of custom loaders for user-specific data sets.

SpecViz allows spectra to be easily plotted and examined. It supports
flexible spectral units conversions, custom plotting attributes, interactive
selections, multiple plots, and other features.

SpecViz notably includes a measurement tool for spectral lines which
enables the user, with a few mouse actions, to perform and record measurements.
It has a model fitting capability that enables the user to create simple
(e.g., single Gaussian) or multi-component models (e.g., multiple Gaussians for
emission and absorption lines in addition to regions of flat continuua).
SpecViz incorporates various methods for fitting such models to data. For more
details, see :ref:`doc_model_fitting`. The ability to overlay line label values
is also supported. SpecViz also allows for overplotting or combining of spectra.

SpecViz will soon include the ability to:

- Measure the average of multiple spectra, detrending, and apply Fourier filters.
- Interactively renormalize data from spectral templates.
- And more...


Installation and Setup
----------------------

.. toctree::
   :maxdepth: 2

   installation
   launching


Using SpecViz
-------------

.. toctree::
   :maxdepth: 2

   getting_started
   unit_conversion
   arithmetic-layer
   loader_wizard
   model_fitting
   statistics
