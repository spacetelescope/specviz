import os

from ...core.plugin import Plugin
from qtpy.uic import loadUi


class Statistics(Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", "statistics", "statistics.ui")), self)

        # Include an action that can be added to the plugin bar
        self.add_to_plugin_bar()

