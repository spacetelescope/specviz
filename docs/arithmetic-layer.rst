.. _specviz-start:

Basic Arithmetic
================

Launching Arithmetic Editor
---------------------------

Lets start by loading the arithmetic layer widget located on the tool bar.
Upon clicking you will be prompted with the arithmetic dialog

(Add image of dialog)

From this dialog you can add, edit or remove arithmetic items from the
editor. We will start by clicking the New Arithmetic Attribute button located in 
top left hand corner of the Editor dialog. Upon clicking you will be prompted with
the editor dialog

(Add image of dialog)

Editing Arithmetic
------------------

Once the Arithmetic widget is launched, spectra and their components can be added
here by typing the names directly surrounded by '{}' or by selecting the spectrum
in the dropdown bar and clicking insert.

(Image of dialog with red circle around where user enters text)

We are going to take the preloaded spectrum (Name of Spectrum) and create a new spectrum 
that is double the flux of Name of Spectrum and call it Double Name of Spectrum.

(Image of Dialog With all fields populated)

To validate arithmetic, click the OK button located at the bottom right hand corner of the
dialog box. Warning(If the python syntax is invalid, the editor will not allow you to continue).
Now, there will be a new data item located in the data collection called Double Name of Spectrum.

(Image pointing to new data object)

To show the result in the plotting window, select the data item by clicking the box next Double
Name of Spectrum.

(Image with both data items plotted)

This is a very simple example of the arithmetic you can perform with the SpecViz arithmetic editor.
Any valid python expression can be parsed by the editor as long as the result of the expression is
a SpecUtils Spectrum1D (make SpecUtils Spectrum1D a hyperlink) object.