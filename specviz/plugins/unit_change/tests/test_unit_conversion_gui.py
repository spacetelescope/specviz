from qtpy import QtCore
from qtpy.QtWidgets import QDialogButtonBox


def get_ucd(specviz_gui):
    """
    Get the unit conversion dialog instance and return it
    """
    ucd = specviz_gui.current_workspace._plugins['Unit Change Plugin']

    ucd.show()
    return ucd


def test_spectral_custom_units_correct(specviz_gui, qtbot):
    """
    Accept valid custom units
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    ucd.ui.comboBox_spectral.setCurrentIndex(0)
    assert ucd.ui.comboBox_spectral.currentText() == ucd.spectral_axis_unit_equivalencies_titles[0]

    ucd.ui.comboBox_spectral.setCurrentIndex(ucd.ui.comboBox_spectral.count()-1)
    assert ucd.ui.comboBox_spectral.currentText() == "Custom"

    ucd.ui.line_custom_spectral.setText("m")
    assert ucd.on_accepted() == True


def test_spectral_custom_units_incorrect(specviz_gui, qtbot):
    """
    Reject invalid custom units
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    ucd.ui.comboBox_spectral.setCurrentIndex(ucd.ui.comboBox_spectral.count() - 1)
    assert ucd.ui.comboBox_spectral.currentText() == "Custom"

    ucd.ui.line_custom_spectral.setText("feet")
    assert ucd.on_accepted() == False


def test_spectral_accept_works_correctly(specviz_gui, qtbot):
    """
    Accept works for units in combobox
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    ucd.ui.comboBox_spectral.setCurrentIndex(0)
    assert ucd.ui.comboBox_spectral.currentText() == ucd.spectral_axis_unit_equivalencies_titles[0]

    # Press accept
    qtbot.mouseClick(ucd.ui.buttonBox.button(QDialogButtonBox.Ok), QtCore.Qt.LeftButton)
    assert ucd.hub.plot_widget.spectral_axis_unit == ucd.spectral_axis_unit_equivalencies[0]


def test_spectral_cancel_works_correctly(specviz_gui, qtbot):
    """
    Make sure units are not changed after cancel
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    original_spectral_unit = ucd.hub.plot_widget.spectral_axis_unit

    ucd.ui.comboBox_spectral.setCurrentIndex(ucd.ui.comboBox_spectral.count() - 1)
    assert ucd.ui.comboBox_spectral.currentText() == ucd.spectral_axis_unit_equivalencies_titles[
        ucd.ui.comboBox_spectral.count() - 1]

    # Press cancel
    qtbot.mouseClick(ucd.ui.buttonBox.button(QDialogButtonBox.Cancel), QtCore.Qt.LeftButton)
    assert ucd.hub.plot_widget.spectral_axis_unit == original_spectral_unit


def test_flux_custom_units_correct(specviz_gui, qtbot):
    """
    Accept valid custom units
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    ucd.ui.comboBox_units.setCurrentIndex(0)
    assert ucd.ui.comboBox_units.currentText() == ucd.data_unit_equivalencies_titles[0]

    ucd.ui.comboBox_units.setCurrentIndex(ucd.ui.comboBox_units.count() - 1)
    assert ucd.ui.comboBox_units.currentText() == "Custom"

    ucd.ui.line_custom_units.setText("Jy")
    assert ucd.on_accepted() == True


def test_flux_custom_units_incorrect(specviz_gui, qtbot):
    """
    Reject invalid custom units
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    ucd.ui.comboBox_units.setCurrentIndex(ucd.ui.comboBox_units.count() - 1)
    assert ucd.ui.comboBox_units.currentText() == "Custom"

    ucd.ui.line_custom_units.setText("feet")
    assert ucd.on_accepted() == False


def test_flux_accept_works_correctly(specviz_gui, qtbot):
    """
    Accept works for units in combobox
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    ucd.ui.comboBox_units.setCurrentIndex(0)
    assert ucd.ui.comboBox_units.currentText() == ucd.data_unit_equivalencies_titles[0]

    qtbot.mouseClick(ucd.ui.buttonBox.button(QDialogButtonBox.Ok), QtCore.Qt.LeftButton)
    assert ucd.hub.plot_widget.data_unit == ucd.data_unit_equivalencies[0]


def test_flux_cancel_works_correctly(specviz_gui, qtbot):
    """
    Make sure units are not changed after cancel
    """
    ucd = get_ucd(specviz_gui)
    qtbot.addWidget(ucd)

    original_flux_unit = ucd.hub.plot_widget.data_unit

    ucd.ui.comboBox_units.setCurrentIndex(ucd.ui.comboBox_units.count() - 1)
    assert ucd.ui.comboBox_units.currentText() == ucd.data_unit_equivalencies_titles[
        ucd.ui.comboBox_units.count() - 1]

    qtbot.mouseClick(ucd.ui.buttonBox.button(QDialogButtonBox.Cancel), QtCore.Qt.LeftButton)
    assert ucd.hub.plot_widget.data_unit == original_flux_unit
