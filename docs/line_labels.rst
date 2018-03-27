.. _doc_line_labels:

Spectral line labels
====================

SpecViz can display spectral line identifications ("Line labels") on top of
spectral data being displayed. Line identifications are supplied by line
lists. There is a set of line lists already included in the distribution,
and the user can read his/hers own line lists as text files formatted
in Astropy's ECSV format.

One a spectrum is displayed in the plot window, clicking on the green
"Line Labels" button in the main menu bar will bring up a floating
window which contains the functionality to manage the line lists.


Selecting line lists
^^^^^^^^^^^^^^^^^^^^

Use the drop-down menu to select a line list. Alternatively, use the
File menu button (the yellow folder) to read a line list from a
user-supplied file.

Currently, the following line lists are supplied within the package
and available via the drop-down menu:

========================= ========= ========================
Line list                 N lines    Wavelength range
========================= ========= ========================
Atomic-Ionic                   42    0.97  -  3.95 micron
CO                             66    1.56  -  2.51 micron
H-He                          145    0.72  -  3.74 micron
H2                            226    1.09  -  3.99 micron
Common Stellar                 95    1,215 - 10,938 Angstrom
Common Nubular                 51    3,430 -  7,130 Angstrom
ILSS                       25,800    2,950 - 13,160 Angstrom
Reader-Corliss             46,646      16  - 39,985 Angstrom
========================= ========= ========================

Once a line list is selected, a dialog pop-up will ask what is the wavelength
range one wants to read from the list. The dialog is populated by default
with the wavelength range spanned by the spectrum being displayed. Typing in
new values in the dialog text fields will retain then during subsequent uses
of the dialog, until they are re-typed again.

The dialog will display the actual number of lines that will be read from
the list. Large numbers of lines trigger an alert, in the form of red text.

The two large lists must be handled with care, because if one attempts to read
or select the entire list, some functionality may be affected adversely and
become very slow. More on that later. It is recommended that small wavelength
ranges be used with those lists, in a way that no more than about 2,000 lines
be read.


Line list management
^^^^^^^^^^^^^^^^^^^^

Each line list, once read, ends up in a table that is placed under a separate
tab. The tab name is the list name. Each tabbed panel contains several sections,
described below:

#. Header with descriptive information on the line list.
#. The table itself. The exact column names and contents are list-dependent. Column
   headers can be clicked; that way, the column is sorted in ascending/descending
   order upon successive clicks. Hovering the mouse on a column heading may bring
   additional information on the column, such as units.
#. Control section. This contains a number of controls to help configure the display
   of the selected lines in the table

Specific lines or groups of lines are selected in the table with the standard selection
gestures provided by the underlying operating system. To select all lines in a table,
click on the upper left corner of the table. To un-select all lines in a table, use the
'Deselect' button in the control section.

The 'Color', 'Height', and 'Redshift' controls allow the customization of the plot of
the currently selected lines. 'Height' is interpreted as the fractional height on the
plot window. 'Redshift' can be interpreted in either 'z' or 'km/s' units, according to
the corresponding selector.


