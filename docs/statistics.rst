.. _specviz-stats_sidebar:

.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

Statistics
==========

11 statistic/analysis functions are calculated using the input spectrum
or specified region of interest, depending on what is selected in the
left sidebar. To get the statistics of a spectrum, select it on the
:ref:`data list <specviz-data-list>` on the left panel.

The user can calculate statistics for a selected region of a spectrum.
First, a `"Region of Interest" is selected <specviz_regions>`_.  Once this
is done, the statistics are automatically calculated and displayed in the left
sidebar. If a region of interest is selected, the statistic
calculations are updated when that region of interest is changed.

.. warning::
    If there are :ref:`regions of interest (ROI) <specviz-regions>` in the plot,
    the statistics are derived from the data points under the **active** region of interest.
    Information about the region is displayed at the bottom of the statistics panel.
    Currently it is not possible to select multiple ROIs thus the statistics pertain to the
    single active ROI. If there are no ROIs added to the plot, the statistics will be calculated
    for the entire spectrum.

Types of Statistics
-------------------

Currently there are three types of statistics:
    - Generic:
        - ``Mean``
        - ``Median``
        - ``Std Dev``
        - ``SNR``
        - ``Max Flux``
        - ``Min Flux``
        - ``Count total``
    - Continuum Subtracted:
        Appends ``FWHM`` and ``Centroid`` to the Generic statistics.
    - Continuum Normalized:
        Appends ``Eq Width`` the Generic statistics.

You can swap between the different types of statistics by using the drop down menu
at the top of the statistics sidebar.



List of statistics
------------------

The following statistics are calculated:

========================= =======================================
Statistics                Function
========================= =======================================
Mean                      `~astropy.units.Quantity.mean`
Median                    `~numpy.median`
Std Dev                   `~astropy.units.Quantity.std`
Centroid                  `~specutils.analysis.centroid`
RMS (Calculated)          ``~numpy.sqrt(flux.dot(flux) / len(flux))``
SNR                       `~specutils.analysis.snr`
FWHM                      `~specutils.analysis.fwhm`
Eq Width                  `~specutils.analysis.equivalent_width`
Max                       `~astropy.units.quantity.Quantity.max`
Min                       `~astropy.units.quantity.Quantity.min`
Count Total               `~specutils.analysis.line_flux`
========================= =======================================

