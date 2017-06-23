"""
Manage and execute the various statistical operations
"""
from ..ui.widgets.plugin import Plugin
from qtpy.QtWidgets import (QGroupBox, QHBoxLayout, QPushButton, QRadioButton,
                            QVBoxLayout, QTreeWidget, QTreeWidgetItem)
from qtpy.QtCore import Qt
from ..core.comms import dispatch, DispatchHandle

import numpy as np


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
        self.tree_widget_dq.itemClicked.connect(self._toggle_bit)

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

    def _toggle_bit(self, item, col=0):
        root = self.tree_widget_dq.invisibleRootItem()
        layer = self.current_layer
        current_bitmask = np.zeros_like(layer._bit_mask)
        for item in [root.child(j) for j in range(root.childCount())]:
            if bool(item.checkState(col)):
                current_bitmask |= layer._bit_mask & (1 << item.data(0, Qt.UserRole))

        layer.mask = current_bitmask.astype(bool)

        self.active_window.update_plot(layer)

    @DispatchHandle.register_listener("on_updated_rois")
    def toggle_mask_button(self, rois):
        if rois:
            self.button_mask_data.setEnabled(True)
            self.button_unmask_data.setEnabled(True)
        else:
            self.button_mask_data.setEnabled(False)
            self.button_unmask_data.setEnabled(False)

    @DispatchHandle.register_listener("on_selected_layer", "on_changed_layer")
    def load_dq_flags(self, layer_item=None, layer=None):
        self.tree_widget_dq.clear()
        if layer_item is None and layer is None:
            return

        layer = layer_item.data(0, Qt.UserRole)
        if layer is not None:
            if layer.mask_def is not None:
                for row in layer.mask_def:
                    new_item = QTreeWidgetItem()
                    new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable)
                    new_item.setCheckState(0, Qt.Checked)
                    new_item.setText(0, str(row['BIT']))
                    new_item.setData(0,Qt.UserRole, row['BIT'])
                    new_item.setText(1, row['NAME'])
                    new_item.setText(2, row['DESCRIPTION'])
                    self.tree_widget_dq.addTopLevelItem(new_item)




class UiMaskEditorPlugin:
    def __init__(self, plugin):
        plugin.group_box_mask = QGroupBox("Binary Mask")

        plugin.group_box_mask_layout = QVBoxLayout(plugin.group_box_mask)
        plugin.group_box_mask_layout.setContentsMargins(10, 0, 0, 0)
        plugin.group_box_mask_layout.setSpacing(0)

        plugin.radio_horizontal_layout = QHBoxLayout()
        plugin.radio_horizontal_layout.setContentsMargins(10, 0, 0, 0)
        plugin.radio_horizontal_layout.setSpacing(0)

        plugin.radio_show_mask = QRadioButton("Show Masked Data")
        plugin.radio_show_mask.setChecked(False)
        plugin.radio_horizontal_layout.addWidget(plugin.radio_show_mask)
        plugin.group_box_mask_layout.addLayout(plugin.radio_horizontal_layout)

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
        plugin.group_box_mask_layout.addLayout(plugin.layout_horizontal_mask_button)
        # plugin.layout_vertical.setContentsMargins(11, 11, 11, 11)
        # plugin.setMaximumHeight(120)

        plugin.group_box_dq = QGroupBox("Data Quality Flags")
        plugin.group_box_dq_layout = QVBoxLayout(plugin.group_box_dq)
        plugin.group_box_dq_layout.setContentsMargins(10, 0, 0, 0)

        plugin.tree_widget_dq = QTreeWidget()
        plugin.tree_widget_dq.setColumnCount(3)
        plugin.tree_widget_dq.headerItem().setText(0, "Bit")
        plugin.tree_widget_dq.headerItem().setText(1, "Name")
        plugin.tree_widget_dq.headerItem().setText(2, "Description")
        plugin.group_box_dq_layout.addWidget(plugin.tree_widget_dq)
        # new_item = QTreeWidgetItem()
        # new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable)
        # new_item.setCheckState(0, Qt.Checked)
        # new_item.setText(0, "0")
        # new_item.setText(1, "NOPLUG")
        # new_item.setText(2, "Fiber not listed in plugmap file")
        # plugin.tree_widget_dq.addTopLevelItem(new_item)


        plugin.layout_vertical.addWidget(plugin.group_box_mask)
        plugin.layout_vertical.addWidget(plugin.group_box_dq)


