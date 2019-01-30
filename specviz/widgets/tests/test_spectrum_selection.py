from qtpy.QtCore import Qt

from ..spectrum_selection import SpectrumSelection


def test_spectrum_selection(specviz_gui):

    spec_select = SpectrumSelection(specviz_gui.current_workspace)

    # Check starting state
    assert spec_select._selected == False
    assert spec_select._model.rowCount() == 0

    # Populate with some arbitrary names
    names = ['a', 'b', 'c', 'd', 'e', 'f']
    spec_select.populate(names)
    assert spec_select._model.rowCount() == len(names)

    # Simulate the action that occurs when clicking "Open"
    spec_select._confirm_selection()
    assert spec_select._selected == True
    assert spec_select.get_selected() == names

    spec_select.close()


def test_deselect_all(qtbot, specviz_gui):

    spec_select = SpectrumSelection(specviz_gui.current_workspace)

    # Populate with some arbitrary names
    names = ['a', 'b', 'c', 'd', 'e', 'f']
    spec_select.populate(names)

    qtbot.mouseClick(spec_select.deselectAllButton, Qt.LeftButton)
    # Simulate the action that occurs when clicking "Open"
    spec_select._confirm_selection()

    assert spec_select.get_selected() == []

    spec_select.close()


def test_deselect_one(specviz_gui):

    spec_select = SpectrumSelection(specviz_gui.current_workspace)

    names = ['a', 'b', 'c', 'd', 'e', 'f']
    spec_select.populate(names)

    # Simulate unchecking a single item from the list
    item = spec_select._model.item(1)
    item.setCheckState(Qt.Unchecked)

    # Simulate the action that occurs when clicking "Open"
    spec_select._confirm_selection()
    assert spec_select.get_selected() == names[:1] + names[2:]

    spec_select.close()


def test_select_all(qtbot, specviz_gui):

    spec_select = SpectrumSelection(specviz_gui.current_workspace)

    names = ['a', 'b', 'c', 'd', 'e', 'f']
    spec_select.populate(names)

    # 'Manually' uncheck all of the boxes in the list
    for index in range(spec_select._model.rowCount()):
        item = spec_select._model.item(index)
        item.setCheckState(Qt.Unchecked)

    # Now click the 'Select All' button
    qtbot.mouseClick(spec_select.selectAllButton, Qt.LeftButton)
    # Simulate the action that occurs when clicking "Open"
    spec_select._confirm_selection()

    assert spec_select.get_selected() == names

    spec_select.close()
