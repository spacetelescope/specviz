import os

from qtpy.uic import loadUi
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog
from qtpy.QtGui import QStandardItemModel, QStandardItem


class SpectrumSelection(QDialog):
    """
    A widget providing a simple dialog for selecting spectra to be loaded.

    The widget itself knows nothing about spectral data objects, but instead
    just presents a list of strings which represent the names of the available
    spectra, and returns a list of strings which represent the names of the
    spectra that were actually selected.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "ui", "spectrum_selection.ui")), self)

        self.setWindowTitle('Spectrum Selection')

        self._model = QStandardItemModel(self.spectrumList)
        self.spectrumList.setModel(self._model)
        self._selected = False

        self.buttonBox.accepted.connect(self._confirm_selection)

        self.selectAllButton.clicked.connect(self._select_all)
        self.deselectAllButton.clicked.connect(self._deselect_all)

    def populate(self, names):
        """
        Add a list of names to be displayed as list items in the dialog

        Parameters
        ----------
        names : `list`
            The list of names to be populated in the dialog
        """
        for s in names:
            item = QStandardItem(s)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self._model.appendRow(item)

    def get_selected(self):
        """
        Get the list of names that were actually checked when the dialog closes

        This method will return an empty list in the following cases:
            * No items were selected when the dialog closes
            * The "Cancel" button was hit by the user instead of "Open"
            * This method is called before the dialog closes

        Returns
        -------
        names : `list`
            The list of names that were selected when the dialog closes
        """
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
    # This code is purely for enabling development and debugging of the widget
    import sys
    from qtpy.QtWidgets import QApplication

    app = QApplication([])
    s = SpectrumSelection()
    s.populate(['a', 'b', 'c', 'd', 'e', 'f'])
    s.show()
    app.exec_()
