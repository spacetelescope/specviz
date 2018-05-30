from qtpy.QtCore import Qt

from specviz.widgets.main_window import UiMainWindow


def test_start_main_window(qtbot):
    """
    Test the ability to start the application.
    """
    window = UiMainWindow()
    window.show()

    qtbot.addWidget(window)

    assert "Untitled Workspace" in window.windowTitle()
