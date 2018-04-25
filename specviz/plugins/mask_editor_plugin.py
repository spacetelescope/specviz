"""
View and edit bad pixels.
"""
import os
import numpy as np
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import (QCheckBox, QGroupBox, QHBoxLayout, QPushButton,
                            QTreeWidget, QTreeWidgetItem, QVBoxLayout)
from qtpy.uic import loadUi

from ..core.events import dispatch
from ..widgets.plugin import Plugin
from ..widgets.utils import UI_PATH

LINE_EDIT_CSS = "QLineEdit {background: #DDDDDD; border: 1px solid #cccccc;}"


class MaskEditorPlugin(Plugin):
    """
    UI to view and edit bad pixels
    """
    name = "Mask Editor"
    location = "right"

    def setup_ui(self):
        # UiMaskEditorPlugin(self)
        loadUi(os.path.join(UI_PATH, "mask_editor_plugin.ui"), self.contents)

    def setup_connections(self):
        self.contents.button_mask_data.clicked.connect(self._mask_data)
        self.contents.button_unmask_data.clicked.connect(self._unmask_data)
        self.contents.checkbox_show_mask.toggled.connect(self._toggle_mask)
        self.contents.tree_widget_dq.itemClicked.connect(self._toggle_bit)

    def _mask_data(self):
        layer = self.current_layer
        current_window = self.active_window
        roi_mask = current_window.get_roi_mask(layer=layer)
        current_item = self.contents.tree_widget_dq.currentItem()
        if current_item is not None:
            bit = current_item.data(0, Qt.UserRole)
            layer.meta['bitmask'][roi_mask] |= (1 << bit)
            layer.mask = layer.meta['bitmask'].astype(bool)
            current_window.update_plot(layer)

    def _unmask_data(self):
        layer = self.current_layer
        current_window = self.active_window
        roi_mask = current_window.get_roi_mask(layer=layer)
        current_item = self.contents.tree_widget_dq.currentItem()
        if current_item is not None:
            bit = current_item.data(0, Qt.UserRole)
            layer.meta['bitmask'][roi_mask] &= ~(1 << bit)
            layer.mask = layer.meta['bitmask'].astype(bool)
            current_window.update_plot(layer)

    def _toggle_mask(self, state):
        if self.active_window is not None:
            layer = self.current_layer
            current_window = self.active_window
            current_window.disable_mask = not state
            current_window.set_active_plot(layer)

    def _toggle_bit(self, item, col=0):
        if col != 0:
            return

        root = self.contents.tree_widget_dq.invisibleRootItem()
        layer = self.current_layer
        current_bitmask = np.zeros_like(layer.masked_data, dtype=np.int)
        bitmask = layer.meta.get('bitmask', np.zeros(layer.masked_data.shape[0], dtype=np.int))
        for item in [root.child(j) for j in range(root.childCount())]:
            if bool(item.checkState(col)):
                current_bitmask |= bitmask & (1 << item.data(0, Qt.UserRole))

        layer.mask = current_bitmask.astype(bool)

        self.active_window.update_plot(layer)

    @dispatch.register_listener("on_updated_rois")
    def toggle_mask_button(self, rois):
        if rois:
            self.contents.button_mask_data.setEnabled(True)
            self.contents.button_unmask_data.setEnabled(True)
        else:
            self.contents.button_mask_data.setEnabled(False)
            self.contents.button_unmask_data.setEnabled(False)

    @dispatch.register_listener("on_changed_layer")
    def load_dq_flags(self, layer_item=None, layer=None):
        self.contents.tree_widget_dq.clear()
        if layer_item is None and layer is None:
            return

        layer = layer_item.data(0, Qt.UserRole)
        if layer is not None:
            if layer.meta.get('mask_def') is not None:
                for row in layer.meta['mask_def'].filled():
                    new_item = QTreeWidgetItem()
                    new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable)
                    new_item.setCheckState(0, Qt.Checked)
                    new_item.setText(0, str(row['BIT']))
                    new_item.setData(0,Qt.UserRole, row['BIT'])
                    new_item.setText(1, row['NAME'])
                    new_item.setText(2, row['DESCRIPTION'])
                    self.contents.tree_widget_dq.addTopLevelItem(new_item)
            else:
                new_item = QTreeWidgetItem()
                new_item.setFlags(new_item.flags() | Qt.ItemIsUserCheckable)
                new_item.setCheckState(0, Qt.Checked)
                new_item.setText(0, str(0))
                new_item.setData(0, Qt.UserRole, 0)
                new_item.setText(1, 'BAD_PIXEL')
                new_item.setText(2, 'A bad pixel')
                self.contents.tree_widget_dq.addTopLevelItem(new_item)
