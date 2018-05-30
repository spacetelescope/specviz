from qtpy.QtCore import Qt


def test_start_main_window(qtbot):
    """
    Test the ability to start the application.
    """
    from specviz.widgets.main_window import UiMainWindow

    window = UiMainWindow()
    window.show()

    assert "Untitled Workspace" in window.windowTitle()
