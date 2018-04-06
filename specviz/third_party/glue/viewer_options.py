import os

from qtpy.QtWidgets import QWidget

from glue.core.data_combo_helper import ComponentIDComboHelper
from glue.utils.qt import load_ui
from glue.external.echo import SelectionCallbackProperty
from glue.external.echo.qt import connect_combo_selection

__all__ = ["OptionsWidget"]


class OptionsWidget(QWidget):

    file_att = SelectionCallbackProperty()

    def __init__(self, parent=None, data_viewer=None):

        super(OptionsWidget, self).__init__(parent=parent)

        self.ui = load_ui('viewer_options.ui', self,
                          directory=os.path.dirname(__file__))

        self.file_helper = ComponentIDComboHelper(self, 'file_att',
                                                  data_collection=data_viewer._data)

        connect_combo_selection(self, 'file_att', self.ui.combo_file_attribute)

    def set_data(self, data):
        self.file_helper.set_multiple_data([data])
