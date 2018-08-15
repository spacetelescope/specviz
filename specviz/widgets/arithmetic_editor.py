import astropy.units as u
import ast
import numpy as np
import os
from PyQt5.uic import loadUi
from qtpy.QtWidgets import (QMainWindow,QInputDialog,QApplication, QDialog,
                            QComboBox, QPushButton, QTreeWidget, QTreeWidgetItem)
from specutils import Spectrum1D
import sys

# from ..utils import UI_PATH

UI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "qt", "ui"))

class EquationEditor(QDialog):
    def __init__(self, data_dict, parent=None):
        super(EquationEditor, self).__init__(parent)
        loadUi(os.path.join(UI_PATH, 'arithmetic_editor.ui'), self)
        self.data_dict = data_dict
        self.button_add_derived.clicked.connect(self.showDialog)
                
    def set_equation(self, eq_name, eq_expression):
        new_row = QTreeWidgetItem()
        new_row.setText(0, eq_name)
        new_row.setText(1, eq_expression)

        self.list_derived_components.addTopLevelItem(new_row)

    def showDialog(self):   
        self.editor = Editor(self, parent=self)     
    
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
    
    def __init__(self, equation_editor, parent=None):
        super(Editor, self).__init__(parent)
        loadUi(os.path.join(UI_PATH,'equation_editor.ui'), self)
        
        self._equation_editor = equation_editor

        self.text_label.setPlaceholderText("New attribute name")
        self.expression.setPlaceholderText(self.placeholder_text)

        self.combosel_data.addItems(list(data_dict.keys()))
        
        # Items may change based on type of arithmetic we allow....
        self.combosel_component.addItems(['wavelength', 'velocity',
                                          'frequency', 'flux'])

        self.button_insert.clicked.connect(self._insert_component)

        self.buttonBox.accepted.connect(self._assign_components)

        self.show()
    
    def _get_raw_command(self):
        return str(self.ui.expression.toPlainText())  

    def _insert_component(self):
        label = self.combosel_data.currentText() + '.' + self.combosel_component.currentText()
        self.expression.insertPlainText(label)
    
    def _assign_components(self):
        self.eq_name = self.text_label.text().strip()
        self.eq_expression = self.expression.toPlainText().strip()

        self._equation_editor.set_equation(self.eq_name, self.eq_expression)

if __name__ == "__main__":
    # Build Test Spectra
    data_dict = {'spec1':Spectrum1D(spectral_axis=np.arange(1, 50) * u.nm, flux=np.random.sample(49)),
                 'spec2':Spectrum1D(spectral_axis=np.arange(50, 100) * u.nm, flux=np.random.sample(49))}
    
    app = QApplication(sys.argv)
    m = QMainWindow()
    m.button = QPushButton("Launch Arithmetic Editor", parent=m)
    m.button.pressed.connect(lambda: EquationEditor(data_dict).exec_())
    m.show()
    sys.exit(app.exec_())