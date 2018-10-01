import os

from asteval import Interpreter
from qtpy.QtCore import Signal
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QDialog, QDialogButtonBox
from qtpy.uic import loadUi
import re


class ModelEquationEditorDialog(QDialog):
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "equation_editor_dialog.ui")), self)

        # Create a mapping of the model names and their model objects, this
        # will be used in the evalulation function as namespace objects.
        self._fittable_models = {model.item(idx).text(): model.item(idx).data()
                                 for idx in range(model.rowCount())}

        # Instantiate the validator so we can connect to its signals
        self._validator = EquationValidator()

        # Populate the drop down list with the model names
        self.model_list_combo_box.addItems(self._fittable_models.keys())

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

        # Do an initial validation just to easily update the status text when
        # the dialog is first shown.
        self._validator.validate(self.equation_text_edit.toPlainText(),
                                 self._fittable_models)

    @property
    def result(self):
        return self._validator.result

    def _update_status_text(self, state, status_text):
        """
        Update dialog status text depending on the state of the validator.
        """
        if state == QValidator.Acceptable:
            self.status_label.setText(status_text)
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.status_label.setText(status_text)
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def _parse_variables(self):
        """
        Whenever the text in the text edit box changes, parse and highlight the
        verified model variable names.
        """
        full_string = self.equation_text_edit.toPlainText()

        for var in self._fittable_models.keys():
            if full_string.find(var) >= 0:
                full_string = re.sub(r"\b{}\b".format(var),
                                     "<span style='color:blue; font-weight:bold'>{0}</span>".format(var),
                                     full_string)

        cursor_pos = self.equation_text_edit.textCursor()
        self.equation_text_edit.blockSignals(True)
        self.equation_text_edit.setText(full_string)
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
        # namespace.update({'disp': np.arange(10)})

        aeval = Interpreter(usersyms=namespace)

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
