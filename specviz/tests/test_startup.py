from qtpy import QtCore
from specviz.app import Application


def test_specviz_startup(qtbot):

    app = Application([], dev=True)
    qtbot.addWidget(app.current_workspace)
    qtbot.mouseClick(app.current_workspace, QtCore.Qt.LeftButton)
