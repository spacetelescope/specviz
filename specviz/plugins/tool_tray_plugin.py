"""
Holder for the general UI operations
"""
import os

import numpy as np

from ..analysis.filters import SmoothingOperation
from ..core.events import dispatch
from ..widgets.dialogs import SmoothingDialog
from ..widgets.plugin import Plugin
from ..widgets.utils import ICON_PATH


class ToolTrayPlugin(Plugin):
    """
    UI plugin for the general UI operations
    """
    name = "Tools"
    location = "hidden"
    priority = 0

    _all_categories = {}

    def setup_ui(self):
        self._smoothing_kernel_dialog = SmoothingDialog()

        # ---
        # Selections setup
        # self.add_tool_bar_actions(
        #     name="Box ROI",
        #     description='Add box ROI',
        #     icon_path=os.path.join(ICON_PATH, "Rectangle Stroked-50.png"),
        #     category='Selections',
        #     enabled=False)

        # ---
        # Setup interactions buttons
        # self.add_tool_bar_actions(
        #     name="Measure",
        #     description='Measure tool',
        #     icon_path=os.path.join(ICON_PATH, "Ruler-48.png"),
        #     category='Interactions',
        #     enabled=False)

        # self.add_tool_bar_actions(
        #     name="Average",
        #     description='Average tool',
        #     icon_path=os.path.join(ICON_PATH, "Average Value-48.png"),
        #     category='Interactions',
        #     enabled=False)

        # self.add_tool_bar_actions(
        #     name="Slice",
        #     description='Slice tool',
        #     icon_path=os.path.join(ICON_PATH, "Split Horizontal-48.png"),
        #     category='Interactions',
        #     enabled=False)

        self.button_smooth = self.add_tool_bar_actions(
            name="Smooth",
            description='Smooth tool',
            icon_path=os.path.join(ICON_PATH, "Line Chart-48.png"),
            category='Interactions',
            enabled=False,
            callback=self._smoothing_kernel_dialog.exec_)

        # ---
        # Setup transformations buttons
        # self.add_tool_bar_actions(
        #     name="Log Scale",
        #     description='Log scale plot',
        #     icon_path=os.path.join(ICON_PATH, "Combo Chart-48.png"),
        #     category='Transformations',
        #     enabled=False)

        # ---
        # Setup plot options
        self.add_tool_bar_actions(
            name="Export",
            description='Export plot',
            icon_path=os.path.join(ICON_PATH, "Export-48.png"),
            category='Options',
            enabled=False)

    def setup_connections(self):
        self._smoothing_kernel_dialog.accepted.connect(
            self._perform_smooth)

    def _perform_smooth(self):
        layer = self.current_layer

        smoothing_operation = SmoothingOperation(
            self._smoothing_kernel_dialog.kernel,
            *self._smoothing_kernel_dialog.args)

        raw_data = smoothing_operation(layer.data)

        new_data = layer.__class__(data=raw_data,
                                   unit=layer.unit,
                                   mask=layer.mask,
                                   dispersion=layer.masked_dispersion,
                                   uncertainty=np.zeros(
                                       layer.uncertainty.array.shape),
                                   dispersion_unit=layer.dispersion_unit,
                                   name="Smoothed {}".format(layer.name))

        dispatch.on_add_layer.emit(layer=new_data)

    @dispatch.register_listener("on_activated_window")
    def toggle_enabled(self, window):
        if window:
            self.button_smooth.setEnabled(True)
        else:
            self.button_smooth.setEnabled(False)
