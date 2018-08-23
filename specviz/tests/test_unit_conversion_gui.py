import pytest

from qtpy import QtCore
from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog, QDialogButtonBox

from ..widgets.plotting import UnitChangeDialog

def test_spec_gui(specviz_gui):
    specviz_gui.exec_()

# def test_custom_units_correct(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     uc.ui.comboBox_units.setCurrentIndex(2)
#     assert uc.ui.comboBox_units.currentText() == uc._units_titles[2]
#
#     uc.ui.comboBox_units.setCurrentIndex(uc.ui.comboBox_units.count()-1)
#     assert uc.ui.comboBox_units.currentText() == "Custom"
#
#     uc.ui.line_custom.setText("fT")
#     assert uc.ui.on_accepted() == True
#
#
# def test_custom_units_incorrect(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     uc.ui.comboBox_units.setCurrentIndex(uc.ui.comboBox_units.count() - 1)
#     assert uc.ui.comboBox_units.currentText() == "Custom"
#
#     uc.ui.line_custom.setText("feet")
#     assert uc.ui.on_accepted() == False
#
#
# def test_accept_works_correctly(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     uc.ui.comboBox_units.setCurrentIndex(4)
#     assert uc.ui.comboBox_units.currentText() == uc._units_titles[4]
#
#     qtbot.mouseClick(uc.ui.buttonBox.button(QDialogButtonBox.Ok), QtCore.Qt.LeftButton)
#     assert uc.current_units == uc._units_titles[4]
#
#
# def test_cancel_works_correctly(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     old_units = uc.current_units
#
#     uc.ui.comboBox_units.setCurrentIndex(3)
#     assert uc.ui.comboBox_units.currentText() == uc._units_titles[3]
#
#     qtbot.mouseClick(uc.ui.buttonBox.button(QDialogButtonBox.Cancel), QtCore.Qt.LeftButton)
#     assert uc.current_units == old_units
