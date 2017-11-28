"""
Manage and execute the various statistical operations
"""
import os
import logging

import numpy as np
import pyqtgraph as pg
from qtpy.QtGui import QColor
from qtpy.uic import loadUi

from ..widgets.plugin import Plugin
from ..analysis import statistics
from ..core.events import dispatch
from ..widgets.utils import UI_PATH


class StatisticsPlugin(Plugin):
    """
    UI to manage and execute the statistical operations
    """
    name = "Statistics"
    location = "left"

    def setup_ui(self):
        loadUi(os.path.join(UI_PATH, "statistics_plugin.ui"), self.contents)

    def setup_connections(self):
        pass

    @dispatch.register_listener("on_updated_rois", "on_selected_layer")
    def update_statistics(self, rois=None, *args, **kwargs):
        if rois is None:
            if self.active_window is not None:
                rois = self.active_window._rois
            else:
                rois = []

        current_layer = self._current_layer

        if self.active_window is None or current_layer is None:
            # Clear statistics information
            for att in self.__dict__:
                if 'line_edit' in att:
                    self.__dict__[att].setText("")

            return

        # Set current layer name text
        self.contents.line_edit_current_layer.setText(current_layer.name)

        mask = self.active_window.get_roi_mask(layer=current_layer)

        stat_dict = statistics.stats(current_layer.masked_data.compressed().value,
                                     mask=mask[~current_layer.masked_data.mask] if mask is not None else None)

        self.contents.line_edit_mean.setText("{0:4.4g}".format(
            stat_dict['mean']))
        self.contents.line_edit_median.setText("{0:4.4g}".format(
            stat_dict['median']))
        self.contents.line_edit_std_dev.setText("{0:4.4g}".format(
            stat_dict['stddev']))
        self.contents.line_edit_rms.setText("{0:4.4g}".format(
            stat_dict['rms']))
        self.contents.line_edit_snr.setText("{0:4.4g}".format(
            stat_dict['snr']))
        self.contents.line_edit_total.setText("{0:4.4g}".format(
            stat_dict['total']))
        self.contents.line_edit_data_point_count.setText("{0:4.4g}".format(
            stat_dict['npoints']))

        # Calculate measured statistics if there are three rois
        if len(rois) < 3:
            # So that the rois are not updating all the time, reset the
            # colors of the rois when the number has *just* fallen below 3
            if self.contents.label_measured_error.isHidden():
                [x.setBrush(QColor(0, 0, 255, 50)) for x in rois]
                [x.update() for x in rois]

            self.contents.label_measured_error.show()
            return
        else:
            [x.setBrush(QColor(0, 0, 255, 50)) for x in rois]
            [x.update() for x in rois]

            self.contents.label_measured_error.hide()

        roi_masks = []

        for roi in rois:
            mask = self.active_window.get_roi_mask(layer=current_layer,
                                                   roi=roi)
            roi_masks.append(mask)

        # Always make the ROI that's over the greatest absolute data value
        # orange
        # roi_data_sets, rois, roi_masks = zip(*sorted(
        #     zip(roi_data_sets, rois, roi_masks),
        #     key=lambda x: np.max(np.abs(x[0]))))

        rois[-1].setBrush(pg.mkBrush(QColor(255, 69, 0, 50)))
        rois[-1].update()

        cont1_stat_dict = statistics.stats(current_layer.masked_data.compressed().value,
                                           mask=roi_masks[0])
        cont2_stat_dict = statistics.stats(current_layer.masked_data.compressed().value,
                                           mask=np.concatenate(roi_masks[1:-1]))

        ew, flux, avg_cont = statistics.eq_width(cont1_stat_dict,
                                                 cont2_stat_dict,
                                                 current_layer,
                                                 mask=roi_masks[-1])

        cent = statistics.centroid(current_layer,
                                   avg_cont=avg_cont,
                                   mask=roi_masks[-1])

        stat_dict = {"eq_width": ew, "centroid": cent, "flux": flux,
                     "avg_cont": avg_cont}

        self.contents.line_edit_equivalent_width.setText("{0:4.4g}".format(
            float(stat_dict['eq_width'])))
        self.contents.line_edit_centroid.setText("{0:5.5g}".format(
            float(stat_dict['centroid'])))
        self.contents.line_edit_flux.setText("{0:4.4g}".format(
            float(stat_dict['flux'])))
        self.contents.line_edit_mean_continuum.setText("{0:4.4g}".format(
            float(stat_dict['avg_cont'])))
