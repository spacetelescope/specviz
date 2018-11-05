.. _specviz-unit-conversion:

Unit Conversion
===============

How Unit Conversion Works
-------------------------

Unit Conversion uses the `astropy.units <http://docs.astropy.org/en/v0.2.1/units/index.html>` module in order to convert spectral
axis and flux units.

import astropy.units as u
potential_X_axis_units = u.Unit(original_spectral_units).find_equivalent_units(equivalencies=u.spectral())
potential_Y_axis_units = u.Unit(original_spectral_units).find_equivalent_units(equivalencies=u.spectral_density(self.hub.data_item.spectral_axis[0]))

The GUI comboboxes are then populated by potential_X_axis_units and potential_Y_axis_units, respectively.
The user can then select any of those options - as well as a "Custom" option - and the changes
will be reflected in the plot. If the user selects the "Custom" option, they can type in their own units, and
if the units are accepted by `astropy.units <http://docs.astropy.org/en/v0.2.1/units/index.html>` the unit conversion
dialog box will allow the units to be parsed. However, "Custom" units are checked by
self.hub.plot_widget.is_data_unit_compatible and self.hub.plot_widget.is_spectral_axis_unit_compatible before
any conversion occurs and if these methods return False, the units will not be converted.
