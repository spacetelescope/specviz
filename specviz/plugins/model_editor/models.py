import uuid

import astropy.units as u
import numpy as np
import qtawesome as qta
from qtpy.QtCore import QSortFilterProxyModel, Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel
from specutils import Spectrum1D
from qtpy.QtGui import QValidator
from asteval import Interpreter
from qtpy.QtCore import Signal, Qt


class ModelFittingModel(QStandardItemModel):
    status_changed = Signal(QValidator.State, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._equation = ""

        self.setHorizontalHeaderLabels(["Name", "Value", "Unit", "Fixed"])

        from astropy.modeling.models import Gaussian1D, Linear1D

        a = Gaussian1D()
        l = Linear1D()

        self.add_model(a)
        self.add_model(l)
        self.add_model(Gaussian1D())

    @property
    def items(self):
        return [self.item(idx) for idx in range(self.rowCount())]

    @property
    def equation(self):
        return self._equation

    @equation.setter
    def equation(self, value):
        self._equation = value
        self.evaluate()

    @property
    def fittable_models(self):
        # Recompose the model objects with the current values in each of its
        # parameter rows.
        fittable_models = {}

        for model_item in self.items:
            model_kwargs = {'name': model_item.text(), 'fixed': {}}

            # For each of the children `StandardItem`s, parse out their
            # individual stored values
            for cidx in range(model_item.rowCount()):
                param_name = model_item.child(cidx, 0).data()
                param_value = float(model_item.child(cidx, 1).text())
                param_unit = model_item.child(cidx, 2).data()
                param_fixed = model_item.child(cidx, 3).checkState() == Qt.Checked

                model_kwargs[param_name] = (u.Quantity(param_value, param_unit)
                                            if param_unit is not None else param_value)
                model_kwargs.get('fixed').setdefault(param_name, param_fixed)

            fittable_models[model_item.text()] = model_item.data().__class__(**model_kwargs)

        return fittable_models

    def add_model(self, model):
        model_name = model.__class__.name

        model_count = len([self.item(idx) for idx in range(self.rowCount())
                           if model.__class__.name in self.item(idx).text()])

        model_name = model_name + str(model_count) if model_count > 0 else model_name

        model_item = QStandardItem(model_name)
        model_item.setData(model, Qt.UserRole + 1)

        for para_name in model.param_names:
            # Retrieve the parameter object from the model
            parameter = getattr(model, para_name)

            # Store the name value
            param_name = QStandardItem(parameter.name)
            param_name.setData(parameter.name, Qt.UserRole + 1)
            param_name.setEditable(False)

            # Store the data value of the parameter
            param_value = QStandardItem("{}".format(parameter.value))
            param_value.setData(parameter.value, Qt.UserRole + 1)

            # Store the unit information
            param_unit = QStandardItem("{}".format(parameter.unit))
            param_unit.setData(parameter.unit, Qt.UserRole + 1)
            param_unit.setEditable(False)

            # Store the fixed state of the unit
            param_fixed = QStandardItem()
            param_fixed.setData(parameter.fixed, Qt.UserRole + 1)
            param_fixed.setCheckable(True)
            param_fixed.setEditable(False)

            model_item.appendRow([param_name, param_value, param_unit, param_fixed])

        self.appendRow([model_item, None, None, None])

        # Add this model to the model equation string. By default, all models
        # are simply added together
        self._equation += " + {}".format(model_name) \
            if len(self._equation) > 0 else "{}".format(model_name)

        return model_item.index()

    def reset_equation(self):
        self._equation = ""

        for item in self.items:
            self._equation += " + {}".format(item.text()) \
                if len(self._equation) > 0 else "{}".format(item.text())

    def evaluate(self):
        """
        Validate the input to the equation editor.

        Parameters
        ----------
        string : str
            Plain text representation of the current equation text edit box.
        fittable_models : dict
            Mapping of tree view model variables names to their model instances.
        """
        fittable_models = self.fittable_models

        # Create an evaluation namespace for use in parsing the string
        namespace = {}
        namespace.update(fittable_models)

        # Create a quick class to dump err output instead of piping to the
        # user's terminal. Seems this cannot be None, and must be an object
        # that has a `write` method.
        aeval = Interpreter(usersyms=namespace,
                            err_writer=type("FileDump", (object,),
                                            {'write': lambda x: None}))

        result = aeval(self.equation)

        if len(aeval.error) > 0 or not any((self.equation.find(x) >= 0
                                            for x in fittable_models.keys())):
            if len(aeval.error) > 0:
                status_text = "<font color='red'>Invalid input: {}</font>".format(
                    str(aeval.error[0].get_error()[1]).split('\n')[-1])
            else:
                status_text = "<font color='red'>Invalid input: at least one model must be " \
                              "used in the equation.</font>"
            state = QValidator.Invalid
        else:
            status_text = "<font color='green'>Valid input.</font>"
            state = QValidator.Acceptable

        self.status_changed.emit(state, status_text)

        return result


class ModelFittingProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, p_int, index):
        if index.row() >= 0:
            return False

        return super().filterAcceptsRow(p_int, index)