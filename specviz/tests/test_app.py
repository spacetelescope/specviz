from qtpy.QtCore import Qt


def test_start_main_window():
    """
    Test the ability to start the application.
    """
    from specviz.widgets.main_window import UiMainWindow

    window = UiMainWindow()

    assert "Untitled Workspace" in window.windowTitle()
