.. _specviz_model_fitting:

.. DANGER:: 

      Please note that this version of Specviz is **no longer being actively supported
      or maintained**. The functionality of Specviz is now available and being actively
      developed as part of `Jdaviz <https://github.com/spacetelescope/jdaviz>`_.

Model Fitting
=============

SpecViz includes functionality to fit models to spectra.
It uses astropy’s Models and SpecUtils to do so.
The following models are available in SpecViz:

========================= ==========================================================
SpecViz Model Name        Astropy Model Class
========================= ==========================================================
Const                     `~astropy.modeling.functional_models.Const1D`
Gaussian                  `~astropy.modeling.functional_models.Gaussian1D`
Linear                    `~astropy.modeling.functional_models.Linear1D`
Lorentz                   `~astropy.modeling.functional_models.Lorentz1D`
Voigt                     `~astropy.modeling.functional_models.Voigt1D`
Polynomial                `~astropy.modeling.polynomial.Polynomial1D`
========================= ==========================================================

The models can be fitted with the following fitters:
They can be fit with the following fitting algorithms in astropy

=================== ============================================
SpecViz Fitter Name Astropy Fitter Class
=================== ============================================
Levenberg-Marquardt `~astropy.modeling.fitting.LevMarLSQFitter`
Simplex             `~astropy.modeling.fitting.SimplexLSQFitter`
=================== ============================================

To use a model:

#. Create a new ``model`` by clicking on the "New Model" button on the WorkSpace toolbar.
#. Select the layer you wish to operate on from the combination box at the
   top of the fitting window. For example, you can choose the layer containing your emission
   or absorption line.
#. Create and position a :ref:`region of interest (ROI) <specviz-regions>`. Multiple ROIs can be used.
   SpecViz fits the data under all the ROIs.
#. Select the desired model from the green ``Add Model`` drop-down box to add it to ``Current Models``.
#. If desired, repeat the above step to add additional models.

.. warning::
    The selected model will only fit data points under **all**
    :ref:`regions of interest (ROI) <specviz-regions>`.
    Data points that are not covered by an ROI will not be fitted.
    If multiple ROIs overlap over a data point, its only considered once.
    All data points are fitted if there are no ROIs added to the plot.

To edit model parameters or enter a better first estimate of the model
parameters:

#. If desired, double-click on the model name to rename it. When you see a
   blinking cursor, enter its new name and press "Enter".
#. Expand the model listing under the model name.
#. Double-click on the desired model parameter value in the listing.
   When you see a blinking cursor, enter the new value and press ``Enter``.

To fit a model:

#. Select the layer you wish to operate on from the combination box at the
   bottom of the fitting window.
#. Adjust model parameter values to approximate fit.
#. Click the lock icon next to any parameter to choose whether it should be kept
   fixed (closed lock) or allowed to vary (open lock) during fitting.
#. Click on the settings icon at the bottom of the model fitting window select options
    such as the desired fitter and maximum iterations.
#. Check the model's ``Equation Editor`` by clicking the calculator button.
    It will pop up with the current model arithmetic. Review. edit and press ok when done.
#. Click the blue ``Fit Model`` button at the bottom of the fitting window.
#. The associated model parameters will be adjusted accordingly.

Equation Editor
^^^^^^^^^^^^^^^
The ``Equation Editor`` text box is used to define the relationship between
different models for the same ``model data item``. The editor can be launched by
clicking the calculator Botton at the bottom of the model fitting window. If nothing
is defined, the default is to add all the models together. To describe a non-default
model relationship, adjust the math operators, as shown in the examples below and
then press ``Enter`` to produce the compound model::

    Linear1 + Gaussian1

::

    Linear1 * Gaussian1

::

    Gaussian1 - Gaussian2

The entity that results from lumping together all the models, and combining them
either using the arithmetic behavior expression, or just adding them all together,
is called a "compound model".


Model names
^^^^^^^^^^^

When added to the ``Current Models`` list, a model will receive a default name
that is generated from the model type (as listed in the drop down model selector)
plus a running numerical suffix.

These names can be changed by clicking on the default name and entering a new
name. Note that changing model names will require that any expression in
the ``Equation Editor`` text box be edited accordingly.