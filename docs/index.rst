.. image:: _static/title_horizontal.png

.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

Introduction
============

SpecViz is a tool for visualization and quick-look analysis of 1D astronomical
spectra. It is written in the Python programming language, and therefore can be
run anywhere Python is supported (see :ref:`specviz-installation`). SpecViz is
built on top of the `SpecUtils <https://specutils.rtfd.io>`_ Astropy-affiliated
python library, providing a visual, interactive interface to the analysis
capabilities in that library.

SpecViz allows spectra to be easily plotted and examined. It supports
flexible spectral unit conversions, custom plotting attributes, interactive
selections, multiple plots, and other features.

SpecViz notably includes a measurement tool for spectral lines which
enables the user, with a few mouse actions, to perform and record measurements.
It has a model fitting capability that enables the user to create simple
(e.g., single Gaussian) or multi-component models (e.g., multiple Gaussians for
emission and absorption lines in addition to regions of flat continua).
A typical data-analysis workflow might involve data exploration using SpecViz
and then scripting to create more complex measurements or modeling workflows
using SpecUtils.

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

   loading_data
   exporting
   workspaces_and_plots
   regions
   unit_conversion
   operations
   arithmetic-layer
   model_fitting
   statistics
   line_labels

Advanced
--------

.. toctree::
   :maxdepth: 1

   developer
   api