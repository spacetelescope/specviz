"""
Holder for the general UI operations
"""
import os

from ..ui.widgets.plugin import Plugin
from ..ui.widgets.utils import ICON_PATH
from ..ui.widgets.dialogs import SmoothingDialog
from ..core.comms import dispatch, DispatchHandle

from ..analysis.filters import smooth


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
        self.add_tool_bar_actions(
            name="Box ROI",
            description='Add box ROI',
            icon_path=os.path.join(ICON_PATH, "Rectangle Stroked-50.png"),
            category='Selections',
            enabled=False)

        # ---
        # Setup interactions buttons
        self.add_tool_bar_actions(
            name="Measure",
            description='Measure tool',
            icon_path=os.path.join(ICON_PATH, "Ruler-48.png"),
            category='Interactions',
            enabled=False)

        self.add_tool_bar_actions(
            name="Average",
            description='Average tool',
            icon_path=os.path.join(ICON_PATH, "Average Value-48.png"),
            category='Interactions',
            enabled=False)

        self.add_tool_bar_actions(
            name="Slice",
            description='Slice tool',
            icon_path=os.path.join(ICON_PATH, "Split Horizontal-48.png"),
            category='Interactions',
            enabled=False)

        self.button_smooth = self.add_tool_bar_actions(
            name="Smooth",
            description='Smooth tool',
            icon_path=os.path.join(ICON_PATH, "Line Chart-48.png"),
            category='Interactions',
            enabled=False,
            callback=self._smoothing_kernel_dialog.exec_)

        self.button_mask = self.add_tool_bar_actions(
            name="Mask",
            description="Mask data in current ROI",
            icon_path=os.path.join(ICON_PATH, "Theatre Mask-48.png"),
            category='Interactions',
            enabled=False,
            callback=self._mask_data
        )

        # ---
        # Setup transformations buttons
        self.add_tool_bar_actions(
            name="Log Scale",
            description='Log scale plot',
            icon_path=os.path.join(ICON_PATH, "Combo Chart-48.png"),
            category='Transformations',
            enabled=False)

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
        new_data = smooth(self.current_layer,
                          self._smoothing_kernel_dialog.kernel,
                          *self._smoothing_kernel_dialog.args)

        dispatch.on_add_layer.emit(layer=new_data)

    def _mask_data(self):
        layer = self.current_layer
        roi_mask = self.active_window.get_roi_mask(layer=layer)
        new_data = layer.from_parent(layer, name="Masked {}".format(layer.name))
        new_data.mask = layer.mask | roi_mask

        dispatch.on_add_layer.emit(layer=new_data)

    @DispatchHandle.register_listener("on_activated_window")
    def toggle_enabled(self, window):
        if window:
            self.button_smooth.setEnabled(True)
        else:
            self.button_smooth.setEnabled(False)

    @DispatchHandle.register_listener("on_updated_rois")
    def toggle_mask_button(self, rois):
        if rois:
            self.button_mask.setEnabled(True)
        else:
            self.button_mask.setEnabled(False)
