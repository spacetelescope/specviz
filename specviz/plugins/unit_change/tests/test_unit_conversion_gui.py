import pytest

from qtpy import QtCore
from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog, QDialogButtonBox

from ..unit_change_dialog import UnitChangeDialog

from specviz.plugins.unit_change.unit_change_dialog import UnitChangeDialog

def test_ucd(specviz_gui, qtbot):
    specviz_gui.current_workspace.load_data("/Users/javerbukh/Documents/data_for_specviz/COS_FUV.fits", "HST/COS")
    workspace = specviz_gui.current_workspace
    ucd = UnitChangeDialog(workspace)
    uc = ucd
    uc.show()
    qtbot.addWidget(uc)

    assert uc.ui.comboBox_spectral.currentText() == "Angstrom"

    uc.ui.comboBox_spectral.setCurrentIndex(uc.ui.comboBox_spectral.count()-1)
    assert uc.ui.comboBox_spectral.currentText() == "Custom"



# def test_custom_units_correct(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     uc.ui.comboBox_spectral.setCurrentIndex(2)
#     assert uc.ui.comboBox_spectral.currentText() == uc._units_titles[2]
#
#     uc.ui.comboBox_spectral.setCurrentIndex(uc.ui.comboBox_spectral.count()-1)
#     assert uc.ui.comboBox_spectral.currentText() == "Custom"
#
#     uc.ui.line_custom_spectral.setText("fT")
#     assert uc.ui.on_accepted() == True
#
#
# def test_custom_units_incorrect(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     uc.ui.comboBox_spectral.setCurrentIndex(uc.ui.comboBox_spectral.count() - 1)
#     assert uc.ui.comboBox_spectral.currentText() == "Custom"
#
#     uc.ui.line_custom_spectral.setText("feet")
#     assert uc.ui.on_accepted() == False
#
#
# def test_accept_works_correctly(qtbot):
#     uc = UnitChangeDialog()
#     uc.show()
#     qtbot.addWidget(uc)
#
#     uc.ui.comboBox_spectral.setCurrentIndex(4)
#     assert uc.ui.comboBox_spectral.currentText() == uc._units_titles[4]
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
#     uc.ui.comboBox_spectral.setCurrentIndex(3)
#     assert uc.ui.comboBox_spectral.currentText() == uc._units_titles[3]
#
#     qtbot.mouseClick(uc.ui.buttonBox.button(QDialogButtonBox.Cancel), QtCore.Qt.LeftButton)
#     assert uc.current_units == old_units
