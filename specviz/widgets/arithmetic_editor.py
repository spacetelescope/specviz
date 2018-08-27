import astropy.units as u
import ast
import math
import numpy as np
import os
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt
from qtpy.QtWidgets import (QMainWindow,QInputDialog,QApplication, QDialog,
                            QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem)
from specutils import Spectrum1D
from specviz.core.items import DataItem
import sys
import uuid

# from ..utils import UI_PATH

UI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ui"))

class EquationEditor(QDialog):
    def __init__(self, model, parent=None):
        """Equation editor main dialog. From this view you can add, edit, and remove
        arithmetic attributes.

        Parameters
        ----------
        data_dict: dict
            Dictionary of spectrum 1D objects.
        """
        super(EquationEditor, self).__init__(parent)
        loadUi(os.path.join(UI_PATH, 'arithmetic_editor.ui'), self)
        
        self.model = model
        self.button_add_derived.clicked.connect(self.showDialog)
        self.button_edit_derived.clicked.connect(self.edit_expression)
        self.button_remove_derived.clicked.connect(self.remove_expression)

    def set_equation(self, eq_name=None, eq_expression=None):
        """Place equation in main dialog.

        Parameters
        ----------
        eq_name: str
            Name of the expression
        eq_expression
            Text of raw expression
        """
        # If there is a current item selected in the tree,
        # then see if the name of equation being passed from the
        # editor matches the new of the selected item and edit.
        current_item = self.list_derived_components.currentItem()
        if current_item and eq_name == current_item.text(0):
            current_item.setText(1, eq_expression)
        else:
            new_row = QTreeWidgetItem()
            new_row.setText(0, eq_name)
            new_row.setText(1, eq_expression)

            self.list_derived_components.addTopLevelItem(new_row)
    
    def edit_expression(self):
        """Edit selected expression in main dialog
        """
        current_item = self.list_derived_components.currentItem()
        label = current_item.text(0)
        equation = current_item.text(1)
        
        self.is_editmode = True
        self.editor = Editor(self, label=label, equation=equation, parent=self)

    def remove_expression(self):
        """Remove selected expression in main diaglog
        """
        current_item = self.list_derived_components.currentItem()
        index = self.list_derived_components.indexOfTopLevelItem(current_item)

        self.list_derived_components.takeTopLevelItem(index)

    def showDialog(self):  
        """Show editor
        """ 
        self.editor = Editor(self, parent=self)     

    def find_matches(self, eq_name):
        """Checks for matching names
        """
        matches = self.list_derived_components.findItems(eq_name, Qt.MatchExactly, 0)
        matches = [item.text(0) for item in matches]
        return matches

class Editor(QDialog):
    tip_text = ("<b>Note:</b> Attribute names in the expression should be surrounded "
                "by {{ }} brackets (e.g. {{{example}}}), and you can use "
                "Numpy functions using np.&lt;function&gt;, as well as any "
                "other function defined in your config.py file.<br><br>"
                "<b>Example expressions:</b><br><br>"
                "  - Subtract 10 from '{example}': {{{example}}} - 10<br>"
                "  - Scale '{example}' to [0:1]: ({{{example}}} - np.min({{{example}}})) / np.ptp({{{example}}})<br>"
                "  - Multiply '{example}' by pi: {{{example}}} * np.pi<br>"
                "  - Use masking: {{{example}}} * ({{{example}}} &lt; 1)<br>")

    placeholder_text = ("Type any mathematical expression here - "
                        "you can include attribute names from the "
                        "drop-down below by selecting them and "
                        "clicking 'Insert'.")
    
    def __init__(self, equation_editor, label=None, equation=None, parent=None):
        """Dialog where you specify equation names and expressions.

        Parameters
        ----------
        equation_editor: QDialog
            Instance of EquationEditor
        label: str
            Name of equation
        equation: str
            Expression text
        """
        super(Editor, self).__init__(parent)
        loadUi(os.path.join(UI_PATH,'equation_editor.ui'), self)
        

        self._equation_editor = equation_editor
        self.is_addmode = label is None

        if label is not None:
            self.text_label.setText(label)
            self.text_label.setDisabled(True)
        else:
            self.text_label.setPlaceholderText("New attribute name")
        if equation is not None:
            self.expression.insertPlainText(equation)
        else:
            self.expression.setPlaceholderText(self.placeholder_text)

        # Set options for spec1d objects to select.        
        self.combosel_data.addItems([item.name for item in model])
        # Set options for spec1d attributes.
        self.combosel_component.addItems(['wavelength', 'velocity',
                                          'frequency', 'flux'])

        self.button_insert.clicked.connect(self._insert_component)
        
        self.button_ok.clicked.connect(self._assign_components)
        self.button_cancel.clicked.connect(self._close_dialog)

        self.text_label.textChanged.connect(self._update_status)
        self.expression.textChanged.connect(self._update_status)
        self._update_status()

        self.setModal(True)
        self.show()

    def _get_eq_name(self):
        return self.text_label.text().strip()

    def _get_raw_command(self):
        return self.expression.toPlainText().strip() 

    def _insert_component(self):
        label = self.combosel_data.currentText()
        self.expression.insertPlainText('{' + label + '}' + '.' + self.combosel_component.currentText())
    
    def _assign_components(self):
        # Assign values for name and expression in TreeWidget
        self.eq_name = self._get_eq_name()
        self.eq_expression = self._get_raw_command()
        
        self._equation_editor.set_equation(self.eq_name, self.eq_expression)
        self._close_dialog()
    
    def _close_dialog(self):
        self.close()

    def _item_from_name(self, name):
        return next((x.spectrum for x in model if x.name == name))
    
    def _update_status(self):
        # If the text hasn't changed, no need to check again
        if hasattr(self, '_cache') and self._cache == (self.text_label.text(), self._get_raw_command()):
            return

        if self.text_label.text() == "":
            self.label_status.setStyleSheet('color: red')
            self.label_status.setText("Component name not set")
            self.button_ok.setEnabled(False)
        
        elif (self.is_addmode and
              self.text_label.text() in self._equation_editor.find_matches(self.text_label.text())
        ):
            self.label_status.setStyleSheet('color: red')
            self.label_status.setText("Component name already exists.")
            self.button_ok.setEnabled(False)

        elif self._get_raw_command() == "":
            self.label_status.setText("")
            self.button_ok.setEnabled(False)
        
        else:
            try:
                dict_map = {x.name: "self._item_from_name('{}')".format(x.name) for x in model}
                raw_str = self._get_raw_command()
                print(raw_str.format(**dict_map))
                print(eval(raw_str.format(**dict_map)))
            except SyntaxError:
                self.label_status.setStyleSheet('color: red')
                self.label_status.setText("Incomplete or invalid syntax")
                self.button_ok.setEnabled(False)
            except Exception as exc:
                self.label_status.setStyleSheet('color: red')
                self.label_status.setText(str(exc))
                self.button_ok.setEnabled(False)
            else:
                self.label_status.setStyleSheet('color: green')
                self.label_status.setText("Valid expression")
                self.button_ok.setEnabled(True)
        
        self._cache = self.text_label.text(), self._get_raw_command()

if __name__ == "__main__":
    
    model = [DataItem("My Data Item", data=Spectrum1D(spectral_axis=np.arange(1, 50) * u.nm, flux=np.random.sample(49)), 
                                      identifier=uuid.uuid4()),
             DataItem("My Data Item 2", data=Spectrum1D(spectral_axis=np.arange(50, 100) * u.nm, flux=np.random.sample(49)), 
                                      identifier=uuid.uuid4())]
    app = QApplication(sys.argv)
    m = QMainWindow()
    m.button = QPushButton("Arithmetic", parent=m)
    m.button.pressed.connect(lambda: EquationEditor(model).exec_())
    m.show()
    sys.exit(app.exec_())