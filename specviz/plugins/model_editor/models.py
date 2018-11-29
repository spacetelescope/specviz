import re
from asteval import Interpreter

import astropy.units as u
from astropy.modeling import models
from qtpy.QtCore import QSortFilterProxyModel, Qt, Signal
from qtpy.QtGui import QStandardItem, QStandardItemModel, QValidator


class ModelFittingModel(QStandardItemModel):
    status_changed = Signal(QValidator.State, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._equation = ""

        self.setHorizontalHeaderLabels(["Name", "Value", "Unit", "Fixed"])

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

    def compose_fittable_models(self):
        # Recompose the model objects with the current values in each of its
        # parameter rows.
        fittable_models = {}

        for model_item in self.items:
            model = model_item.data()
            model_name = model_item.text()
            model_kwargs = {'name': model_name, 'fixed': {}}

            if isinstance(model, models.PolynomialModel):
                model_args = [model.degree]
            else:
                model_args = []

            # For each of the children `StandardItem`s, parse out their
            # individual stored values
            for cidx in range(model_item.rowCount()):
                param_name = model_item.child(cidx, 0).data()
                param_value = model_item.child(cidx, 1).data()
                param_unit = model_item.child(cidx, 2).data()
                param_fixed = model_item.child(cidx, 3).checkState() == Qt.Checked

                model_kwargs[param_name] = (u.Quantity(param_value, param_unit)
                                            if param_unit is not None else param_value)
                model_kwargs.get('fixed').setdefault(param_name, param_fixed)

            new_model = model.__class__(*model_args, **model_kwargs)
            fittable_models[model_name] = new_model

        return fittable_models

    @property
    def fittable_models(self):
        return self.compose_fittable_models()

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
            param_value = QStandardItem("{:.5g}".format(parameter.value))
            param_value.setData(parameter.value, Qt.UserRole + 1)

            # Store the unit information
            # param_unit = QStandardItem("{}".format(parameter.unit))
            param_unit = QStandardItem("Plot Units")
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

    def remove_model(self, row):
        """
        Remove an astropy model from the internal qt data model.

        Parameters
        ----------
        row : int
            The row in the qt model that is to be removed.
        """
        # Get the model first so that we can re-parse the equation
        model_item = self.item(row, 0)

        # Remove the model name from the equation
        self.equation = re.sub(
            "(\+|-|\*|\/|=|>|<|>=|<=|&|\||%|!|\^|\(|\))*\s*?({})".format(
                model_item.text()),
            "", self._equation)

        # Remove the model item from the internal qt model
        self.removeRow(row)

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
        fittable_models = self.compose_fittable_models()

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
