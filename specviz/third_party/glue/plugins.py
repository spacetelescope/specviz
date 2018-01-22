"""
Manage plot attributes
"""
import logging
import os
from collections import OrderedDict

from astropy.units import Unit

from ...widgets.utils import ICON_PATH
from ...core.events import dispatch, dispatch
from ...widgets.dialogs import TopAxisDialog, UnitChangeDialog
from ...widgets.plugin import Plugin


class PlotToolsPlugin(Plugin):
    """
    UI plugin to manage plot attributes of the various layers
    """
    name = "Apply to Cube"
    location = "hidden"
    _all_categories = {}

    def setup_ui(self):
        self.button_add_roi = self.add_tool_bar_actions(
            name="Apply to Cube",
            description='Apply the  ',
            icon_path=os.path.join(ICON_PATH, "Merge Vertical-48.png"),
            category=('Selections', 4),
            priority=1,
            callback=lambda: dispatch.on_add_roi.emit(),
            enabled=False)