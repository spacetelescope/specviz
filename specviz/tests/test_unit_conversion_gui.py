import pytest

from qtpy import QtCore
from qtpy.QtWidgets import QMainWindow, QMdiSubWindow, QListWidget, QAction, QDialog, QDialogButtonBox

from ..widgets.plotting import UnitChangeDialog


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
