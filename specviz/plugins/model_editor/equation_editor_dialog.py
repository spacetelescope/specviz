import os

from asteval import Interpreter
from qtpy.QtCore import Signal, Qt
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import QDialog, QDialogButtonBox
from qtpy.uic import loadUi
import re

import astropy.units as u


class ModelEquationEditorDialog(QDialog):
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "equation_editor_dialog.ui")), self)
        self._model_editor_model = model

        # When the insert button is pressed, parse the current text of the
        # combo box and put that variable in the equation.
        self.insert_button.clicked.connect(
            lambda: self.equation_text_edit.textCursor().insertHtml(
                self.model_list_combo_box.currentText()))

        # Whenever the text inside the text edit box changes, do two things:
        # 1. Parse the text and bold/color all verified variable names, and 2.
        # validate that the equation would actually produce a compound model.
        self.equation_text_edit.textChanged.connect(self._parse_variables)

        # Listen for validation updates and change the displayed status text
        # depending on whether the validation is successful.
        self._model_editor_model.status_changed.connect(
            self._update_status_text)

    @property
    def model(self):
        return self._model_editor_model

    @model.setter
    def model(self, value):
        self._model_editor_model = value

    def exec_(self):
        # Populate the drop down list with the model names
        self.model_list_combo_box.clear()
        self.model_list_combo_box.addItems(self.model.compose_fittable_models().keys())

        self.equation_text_edit.setPlainText(self.model.equation)

        # Do an initial validation just to easily update the status text when
        # the dialog is first shown.
        self.model.evaluate()

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
        self.model.equation = full_string

        for var in self.model.compose_fittable_models().keys():
            comp_reg = re.compile(r"\b{}\b".format(var))

            if len(comp_reg.findall(full_string)) > 0:
                full_string = re.sub(r"\b{}\b".format(var),
                                     "<span style='color:blue; font-weight:bold'>{0}</span>".format(var),
                                     full_string)

        # Store the cursor position because setting the html explicitly will
        # reset it to the beginning. Also, disable signals so that setting the
        # text in the box doesn't cause infinite recursion.
        cursor = self.equation_text_edit.textCursor()
        cursor_pos = cursor.position()
        self.equation_text_edit.blockSignals(True)
        self.equation_text_edit.setHtml(full_string)
        self.equation_text_edit.blockSignals(False)
        cursor.setPosition(cursor_pos)
        self.equation_text_edit.setTextCursor(cursor)
        self.equation_text_edit.repaint()
