"""
Manage and execute the various statistical operations
"""
from ..widgets.plugin import Plugin
from qtpy.QtWidgets import (QGroupBox, QHBoxLayout, QPushButton, QRadioButton,
                            QVBoxLayout, QCheckBox)
from qtpy.QtCore import *
from ..core.comms import dispatch, DispatchHandle
from ..analysis import statistics
from qtpy.QtGui import *

import logging
import pyqtgraph as pg
import numpy as np
import astropy.units as u
from functools import reduce


LINE_EDIT_CSS = "QLineEdit {background: #DDDDDD; border: 1px solid #cccccc;}"


class MaskEditorPlugin(Plugin):
    """
    UI to manage and execute the statistical operations
    """
    name = "Mask Editor"
    location = "right"

    def setup_ui(self):
        UiMaskEditorPlugin(self)

    def setup_connections(self):
        self.button_mask_data.clicked.connect(self._mask_data)
        self.button_unmask_data.clicked.connect(self._unmask_data)
        self.radio_show_mask.toggled.connect(self._toggle_mask)

    def _mask_data(self):
        layer = self.current_layer
        current_window = self.active_window
        roi_mask = current_window.get_roi_mask(layer=layer)
        layer.mask[roi_mask] = True
        current_window.update_plot(layer)

    def _unmask_data(self):
        layer = self.current_layer
        current_window = self.active_window
        roi_mask = current_window.get_roi_mask(layer=layer)
        layer.mask[roi_mask] = False
        current_window.update_plot(layer)

    def _toggle_mask(self, state):
        if self.active_window is not None:
            layer = self.current_layer
            current_window = self.active_window
            current_window.disable_mask = not state
            current_window.set_active_plot(layer)

    @DispatchHandle.register_listener("on_updated_rois")
    def toggle_mask_button(self, rois):
        if rois:
            self.button_mask_data.setEnabled(True)
            self.button_unmask_data.setEnabled(True)
        else:
            self.button_mask_data.setEnabled(False)
            self.button_unmask_data.setEnabled(False)



class UiMaskEditorPlugin:
    def __init__(self, plugin):
        plugin.layout_vertical = QVBoxLayout()
        plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)
        plugin.layout_vertical.setSpacing(6)
        plugin.group_box = QGroupBox()

        plugin.contents.setLayout(plugin.layout_vertical)
        plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)

        plugin.group_box_layout = QVBoxLayout(plugin.group_box)
        plugin.group_box_layout.setContentsMargins(10, 0, 0, 0)
        plugin.group_box_layout.setSpacing(0)

        plugin.radio_horizontal_layout = QHBoxLayout()
        plugin.radio_horizontal_layout.setContentsMargins(10, 0, 0, 0)
        plugin.radio_horizontal_layout.setSpacing(0)

        plugin.radio_show_mask = QRadioButton("Show Masked Data")
        plugin.radio_show_mask.setChecked(False)
        plugin.radio_horizontal_layout.addWidget(plugin.radio_show_mask)
        plugin.group_box_layout.addLayout(plugin.radio_horizontal_layout)

        plugin.layout_horizontal_mask_button = QHBoxLayout()
        plugin.layout_horizontal_mask_button.setContentsMargins(0, 0, 0, 0)
        plugin.layout_horizontal_mask_button.setSpacing(6)

        plugin.button_mask_data = QPushButton()
        plugin.button_mask_data.setText("Mask Data")
        plugin.button_mask_data.setToolTip("Mask data in current ROI")
        plugin.button_mask_data.setEnabled(False)

        plugin.button_unmask_data = QPushButton()
        plugin.button_unmask_data.setText("Unmask Data")
        plugin.button_unmask_data.setToolTip("Remove mask from data in current ROI")
        plugin.button_unmask_data.setEnabled(False)

        plugin.layout_horizontal_mask_button.addWidget(plugin.button_mask_data)
        plugin.layout_horizontal_mask_button.addWidget(plugin.button_unmask_data)
        plugin.group_box_layout.addLayout(plugin.layout_horizontal_mask_button)
        # plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)
        plugin.setMaximumHeight(120)

        plugin.layout_vertical.addWidget(plugin.group_box)


