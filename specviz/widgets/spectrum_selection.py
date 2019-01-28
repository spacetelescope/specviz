import os

from qtpy.uic import loadUi
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog
from qtpy.QtGui import QStandardItemModel, QStandardItem


class SpectrumSelection(QDialog):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "ui", "spectrum_selection.ui")), self)

        self.setWindowTitle('Select Spectra to Load')

        self._model = QStandardItemModel(self.spectrumList)
        self.spectrumList.setModel(self._model)
        self._selected = False

        self.buttonBox.accepted.connect(self._confirm_selection)

        self.selectAllButton.clicked.connect(self._select_all)
        self.deselectAllButton.clicked.connect(self._deselect_all)

    def populate(self, spectra):
        for s in spectra:
            item = QStandardItem(s)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self._model.appendRow(item)

    def get_selected(self):
        if not self._selected:
            return []

        selected = []
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        return selected

    def _confirm_selection(self):
        self._selected = True

    def _select_all(self):
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            item.setCheckState(Qt.Checked)

    def _deselect_all(self):
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            item.setCheckState(Qt.Unchecked)


if __name__ == '__main__': # noqa

    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    s = SpectrumSelection()
    s.populate(['a', 'b', 'c', 'd', 'e', 'f'])
    s.show()
    app.exec_()
