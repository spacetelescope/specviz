.. _specviz-stats_sidebar:

Right Sidebar Statistics Display
--------------------------------

11 statistic/analysis functions are calculated using the input spectrum
or  specified region of interest, depending on what is selected in the
left side bar.  If a region of interest is selected, the statistic
calculations are updated when that region of interest is changed.

Mean, median, standard deviation, max and min are calculated using
``numpy.mean``, ``numpy.median``, ``numpy.std``,   ``numpy.ndarray.max``
and ``numpy.ndarray.min`` respectively. The centroid, full width half max,
and equivalent width are calculated using the
:func:`specutils.analysis.centroid`, :func:`specutils.analysis.fwhm`,
:func:`specutils.analysis.equivalent_width` respectively.

The signal to noise ratio is calculated using :func:`specutils.analysis.sn`,
however if no uncertainties have been provided for the input spectrum, this
value will N/A.

The count total field is calculated using :func:`specutils.analysis.line_flux`.