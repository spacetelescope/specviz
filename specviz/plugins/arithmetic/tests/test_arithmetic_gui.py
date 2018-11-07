from qtpy import QtCore

from specviz.plugins.arithmetic.arithmetic_editor import Arithmetic


LeftButton = QtCore.Qt.LeftButton


def test_arithmetic_gui(specviz_gui, qtbot):

    ui = specviz_gui.current_workspace._plugins['Arithmetic']
    # Emulate the button push in the toolbar
    ui.on_action_triggered()

    # Bring up the model editor
    qtbot.mouseClick(ui.button_add_derived, LeftButton)

    editor = ui.editor

    # Test inserting a spectrum
    qtbot.mouseClick(editor.button_insert_spectrum, LeftButton)
    assert editor.expression.toPlainText() == '{Spectrum 1}'
