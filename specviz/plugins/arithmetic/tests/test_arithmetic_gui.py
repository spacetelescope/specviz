from qtpy import QtCore

from specviz.core.hub import Hub
from specviz.plugins.arithmetic.arithmetic_editor import Arithmetic


LeftButton = QtCore.Qt.LeftButton


def test_arithmetic_gui(specviz_gui, qtbot):

    hub = Hub(workspace=specviz_gui.current_workspace)
    # Make sure that there are only 3 data items currently
    assert len(hub.data_items) == 3

    ui = specviz_gui.current_workspace._plugins['Arithmetic']
    # Emulate the button push in the toolbar
    ui.show()

    # Bring up the model editor
    qtbot.mouseClick(ui.button_add_derived, LeftButton)

    editor = ui.editor

    # Test inserting a spectrum
    qtbot.mouseClick(editor.button_insert_spectrum, LeftButton)
    assert editor.expression.toPlainText() == '{' + hub.data_items[0].name + '}'

    # Check the error message for unset attribute
    assert editor.label_status.text() == 'Attribute name not set'
    assert editor.button_ok.isEnabled() == False

    # Now try setting the attribute to something that's already a component
    editor.text_label.setText(str(hub.data_items[0].name))
    assert editor.label_status.text() == 'Component name already exists.'
    assert editor.button_ok.isEnabled() == False

    # Try setting the attribute to a new name
    new_component_name = 'Test Component'
    editor.text_label.setText(new_component_name)
    assert editor.label_status.text() == 'Valid expression'
    assert editor.button_ok.isEnabled() == True

    # Start building up an expression... this should be invalid so far
    editor.expression.insertPlainText(' *')
    assert editor.label_status.text() == 'Incomplete or invalid syntax'
    assert editor.button_ok.isEnabled() == False

    # Finish building an expression
    editor.expression.insertPlainText(' 2')
    assert editor.label_status.text() == 'Valid expression'
    assert editor.button_ok.isEnabled() == True

    # Add the new component
    qtbot.mouseClick(editor.button_ok, LeftButton)
    assert len(hub.data_items) == 4
    assert hub.data_items[-1].name == new_component_name

    # Make sure the computation actually had an effect
    old = hub.data_items[0].spectrum.flux
    new = hub.data_items[-1].spectrum.flux
    assert (new == old*2).all()

    ui.close()
