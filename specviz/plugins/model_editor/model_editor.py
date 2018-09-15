import os

from ...core.plugin import Plugin, plugin_bar
from qtpy.uic import loadUi
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QWidget

import qtawesome as qta


@plugin_bar("Model Editor", icon=QIcon(":/icons/012-file.svg"))
class ModelEditor(QWidget, Plugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        loadUi(os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         ".", "model_editor.ui")), self)

        # Model editing
        from .models import ModelFittingModel, ModelFittingProxyModel

        model_fitting_model = ModelFittingModel()
        # model_fitting_proxy_model = ModelFittingProxyModel()
        # model_fitting_proxy_model.setSourceModel(model_fitting_model)

        self.model_tree_view.setModel(model_fitting_model)

        # def _set_root(idx):
        #     src_idx = model_fitting_proxy_model.mapToSource(idx)
        #     idx = src_idx.siblingAtColumn(1)
        #     self.parameter_tree_view.setRootIndex(idx)

        # self.model_tree_view.selectionModel().currentChanged.connect(_set_root)
