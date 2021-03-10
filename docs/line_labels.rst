.. _doc_line_labels:

.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

Spectral line labels
====================

SpecViz can display spectral line identifications ("Line labels") on top of
spectral data being displayed. Line identifications are supplied by line
lists. There is a set of line lists already included in the distribution,
and the user can read his/hers own line lists as text files formatted
in Astropy's ECSV format.

Once a spectrum is displayed in the plot window, clicking on the
"Line Labels" tab in the plug-in sidebar will give access to the line
labels tool, which contain the functionality to manage the line lists.


Selecting line lists
^^^^^^^^^^^^^^^^^^^^

Use the drop-down menu to select a line list. Alternatively, use the
File menu button to read a line list from a user-supplied file (see
more about that at the end of this page).

Currently, the following line lists are supplied within the package
and available via the drop-down menu:

.. |AA| unicode:: U+0212B

========================= ========= ========================
Line list                 Number    Wavelength range
                          of lines
========================= ========= ========================
Atomic-Ionic                   42    0.97  -  3.95 :math:`{\mu}`
CO                             66    1.56  -  2.51 :math:`{\mu}`
H-He                          145    0.72  -  3.74 :math:`{\mu}`
H2                            226    1.09  -  3.99 :math:`{\mu}`
Common Stellar                 95    1,215 - 10,938 |AA|
Common Nebular                 51    3,430 -  7,130 |AA|
ILSS                       25,800    2,950 - 13,160 |AA|
Reader-Corliss             46,646      16  - 39,985 |AA|
SDSS                           48    1,034 -  8,660 |AA|
========================= ========= ========================

Once a line list is selected, a dialog pop-up will ask what is the wavelength
range one wants to read from the list. The dialog is populated by default
with the wavelength range spanned by the spectrum being displayed. It can also
handle units like energy and frequency. Typing in new values in the dialog text
fields will retain then during subsequent uses of the dialog, until they are re-typed again.

The dialog will display the actual number of lines that will be read from
the list. Large numbers of lines trigger an alert, in the form of red text.

The two large lists provided within the tol must be handled with care, because if
one attempts to read or select the entire list, some functionality may be affected
adversely and become very slow. It is recommended that small wavelength ranges be
used with those lists, in a way that no more than about 2,000 lines be read.


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

List sub-sets
-------------
When at least one line is selected in the table, clicking the 'Create set' button causes
a new list to be built and displayed in a new tab after the 'Original' tab. The 'Original'
tab always contains the entire original list. Successive use of table row selection
gestures and the 'Create set' button, allows the creation of multiple sub sets. Sub-sets
can be created from the 'Original' list, as well as from any other sub-set.

Each list sub-set carries its own group of display controls: color, height, and redshift.
With these, one can customize the appearance of each sub-set on the plot.

The list sub-set capability can be combined with the column sorting and multiple row
selection capabilities to implement hierarchical sorting.

Say, as an example, one wants to display all the Fe lines in blue color, and all the
high intensity Fe lines (if intensity is provided by the line list) in red. One can sort
the original table by species, select the subgroup of Fe lines, and create set #1. Next,
on the #1 set, one sorts by intensity, selects all the high intensity lines, and creates
set #2. One then de-selects everything in the Original set, and selects everything in sets
#1 and #2. Finally, in set #1 one picks the blue color, and in set #2 the red color.
Clicking 'Draw' will then plot everything.


Drawing the line labels
^^^^^^^^^^^^^^^^^^^^^^^

The 'Draw' button accomplishes the actual plotting. It works by finding all the lines
that are selected in all tabs at once. Before performing the actual plotting, it will
first erase all line labels left on screen by previous drawings. The 'Erase' button
performs the same action, with no subsequent drawing.

At the left lower corner of the window, a counter keeps track of the total of lines
selected at any time. The counter becomes red as a warning that a large number of lines
is selected. Plotting a large number of line labels slows down the plot and zoom
functionalities. The user must be aware that the response may become slow when large
numbers of lines are selected.

The drawing operation includes a de-cluttering step. This achieves the dual goal of
making the plot more readable, and faster to zoom/pan/rescale. The de-cluttering
algorithm trades speed for cleverness, and a side effect of that is that, when plotting
sets of lines at different heights on screen, some line labels may disappear even though
they shouldn't. Zooming in will eventually make all line labels visible.

Experience has shown that the perceived speed depends to a certain amount on the particular
hardware and software platform the application is running on. Typically, a slow laptop
can handle a couple of hundred lines with no problem. A faster, multi-core desktop can
be pushed up to perhaps a thousand line labels before performance degrades significantly.


Results
^^^^^^^

The 'Plotted' tab will always contain the lines currently being displayed on the plot.
The contents of this tab can be output to a ECSV file via the Export button on the top
menu bar of the line lists window.

The file thus produced can be directly read by SpecViz via de File button (the yellow
folder icon).


Example of an output file in ECSV format:

::

 # %ECSV 0.9
 # ---
 # datatype:
 # - {name: Wavelength, unit: Angstrom, datatype: float64}
 # - {name: Species, unit: '', datatype: string}
 # meta: !!omap
 # - comments: [Common stellar lines., '', Copyrigtht (C) 1999-2004 by Christian Buil, 'http://www.astrosurf.com/buil/us/spe2/hresol5.htm']
 # schema: astropy-2.0
 Wavelength Species
 1215.67 La
 1238.81 "N V"
 1242.8 "N V"
 1393.76 "Si IV"
 1402.77 "Si IV"
