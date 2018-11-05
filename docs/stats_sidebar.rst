.. _specviz-stats_sidebar:

Right Sidebar Statistics Display
--------------------------------

11 statistic/analysis functions are calculated using the input spectrum
or  specified region of interest, depending on what is selected in the
left side bar.  If a region of interest is selected, the statistic
calculations are updated when that region of interest is changed.

Calcualtions are done using the following functions:

Mean
  astropy.units.Quantity.mean
Median:
  numpy.median
Std Dev:
  astropy.units.Quantity.std
Centroid:
  :func:`specutils.analysis.centroid`
RMS:
  numpy.sqrt(flux.dot(flux) / len(flux))
SNR:
  :func:`specutils.analysis.snr`
FWHM:
  :func:`specutils.analysis.fwhm`
Eq Width:
  :func:`specutils.analysis.equivalent_width`
Max:
  astropy.units.quantity.Quantity.max
Min:
  astropy.units.quantity.Quantity.min
Count Total:
  :func:`specutils.analysis.line_flux`