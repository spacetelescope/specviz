import os

from asteval import Interpreter
from qtpy.QtCore import Signal, Qt
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QDialog, QDialogButtonBox
from qtpy.uic import loadUi
import re

import astropy.units as u


class ModelEquationEditorDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "equation_editor_dialog.ui")), self)
        self._model_editor_model = None
        self._fittable_models = None

        # Instantiate the validator so we can connect to its signals
        self._validator = EquationValidator()

        # When the insert button is pressed, parse the current text of the
        # combo box and put that variable in the equation.
        self.insert_button.clicked.connect(
            lambda: self.equation_text_edit.textCursor().insertHtml(
                self.model_list_combo_box.currentText()))

        # Whenever the text inside the text edit box changes, do two things:
        # 1. Parse the text and bold/color all verified variable names, and 2.
        # validate that the equation would actually produce a compound model.
        self.equation_text_edit.textChanged.connect(
            lambda: self._validator.validate(self.equation_text_edit.toPlainText(),
                                             self._fittable_models))
        self.equation_text_edit.textChanged.connect(self._parse_variables)

        # Listen for validation updates and change the displayed status text
        # depending on whether the validation is successful.
        self._validator.status_changed.connect(self._update_status_text)

    @property
    def model(self):
        return self._model_editor_model

    @model.setter
    def model(self, value):
        self._model_editor_model = value

    @property
    def result(self):
        return self._validator.result

    def exec_(self):
        # Recompose the model objects with the current values in each of its
        # parameter rows.
        self._fittable_models = {}

        for idx in range(self._model_editor_model.rowCount()):
            # Get the base astropy model object
            model_item = self._model_editor_model.item(idx)
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

            self._fittable_models[model_item.text()] = model_item.data().__class__(**model_kwargs)

        # Populate the drop down list with the model names
        self.model_list_combo_box.clear()
        self.model_list_combo_box.addItems(self._fittable_models.keys())

        # Do an initial validation just to easily update the status text when
        # the dialog is first shown.
        self._validator.validate(self.equation_text_edit.toPlainText(),
                                 self._fittable_models)

        super().exec_()

    def _update_status_text(self, state, status_text):
        """
        Update dialog status text depending on the state of the validator.
        """
        self.status_label.setText(status_text)

        if state == QValidator.Acceptable:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        self.button_box.repaint()

    def _parse_variables(self):
        """
        Whenever the text in the text edit box changes, parse and highlight the
        verified model variable names.
        """
        full_string = self.equation_text_edit.toPlainText()

        for var in self._fittable_models.keys():
            comp_reg = re.compile(r"\b{}\b".format(var))

            if len(comp_reg.findall(full_string)) > 0:
                full_string = re.sub(r"\b{}\b".format(var),
                                     "<span style='color:blue; font-weight:bold'>{0}</span>".format(var),
                                     full_string)

        # Store the cursor position because setting the html explicitly will
        # reset it to the beginning. Also, disable signals so that setting the
        # text in the box doesn't cause infinite recursion.
        cursor_pos = self.equation_text_edit.textCursor()
        self.equation_text_edit.blockSignals(True)
        self.equation_text_edit.setHtml(full_string)
        self.equation_text_edit.blockSignals(False)
        self.equation_text_edit.setTextCursor(cursor_pos)


class EquationValidator(QValidator):
    status_changed = Signal(QValidator.State, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._result = None
        self._state = QValidator.Invalid

    @property
    def result(self):
        """
        Returned value from the string evaluation.

        Returns
        -------
        : :class:`~astropy.modeling.CompoundModel`
            The composed compound model generated from the input equation.
        """
        return self._result

    def validate(self, string, fittable_models):
        """
        Validate the input to the equation editor.

        Parameters
        ----------
        string : str
            Plain text representation of the current equation text edit box.
        fittable_models : dict
            Mapping of tree view model variables names to their model instances.
        """
        # Create an evaluation namespace for use in parsing the string
        namespace = {}
        namespace.update(fittable_models)

        # Create a quick class to dump err output instead of piping to the
        # user's terminal. Seems this cannot be None, and must be an object
        # that has a `write` method.
        aeval = Interpreter(usersyms=namespace,
                            err_writer=type("FileDump", (object,),
                                            {'write': lambda x: None}))

        self._result = aeval(string)

        if len(aeval.error) > 0 or not any((string.find(x) >= 0
                                            for x in fittable_models.keys())):
            if len(aeval.error) > 0:
                status_text = "<font color='red'>Invalid input: {}</font>".format(
                    str(aeval.error[0].get_error()[1]).split('\n')[-1])
            else:
                status_text = "<font color='red'>Invalid input: at least one model must be " \
                              "used in the equation.</font>"
            self._state = QValidator.Invalid
        else:
            status_text = "<font color='green'>Valid input.</font>"
            self._state = QValidator.Acceptable

        self.status_changed.emit(self._state, status_text)
