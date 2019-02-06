import numpy as np

from qtpy.QtCore import QEvent, Qt, QThread, Signal, QMutex, QTime
from qtpy.QtWidgets import QMessageBox

from astropy import units as u

from .annotation import LineIDMarker, LineIDMarkerProxy
from .linelist import LineList, WAVELENGTH_COLUMN, \
    REDSHIFTED_WAVELENGTH_COLUMN, \
    MARKER_COLUMN, ID_COLUMN, COLOR_COLUMN, HEIGHT_COLUMN

__all__ = ['LineLabelsPlotter', 'ZoomMarkersThread', 'ZoomEventBuffer']


class LineLabelsPlotter(object):
    """
    Class that encapsulates and handles the gory details of line label
    plotting, and especially, zooming.

    Parameters
    ----------
    linelist_window : :class:`~specviz.plugins.line_labels.linelists_window.LineListsWindow`
        The line list window calling this with data to be plotted.
    """

    def __init__(self, linelist_window, *args, **kwargs):
        super(LineLabelsPlotter, self).__init__(*args, **kwargs)

        self._linelist_window = linelist_window
        self._linelists = self._linelist_window.linelists
        self._plot_widget = self._linelist_window.hub.plot_widget

        # This is normally set to False, except for the brief moment in
        # between the arrivals of a data_unit_changed signal and a
        # sigRangeChanged signal. That situation takes place when the
        # plot units have changed, but the plot widget didn't have time
        # to update it's range yet (as delivered by plot_widget.viewRange).
        # After the arrival of a data_unit_changed, we have to wait for the
        # next sigRangeChanged in order to access the new plot range and
        # use it to re-plot the line labels.
        self._units_changed = False

        # create a new, empty list that will store and help track down
        # which markers are actually being displayed at any time.
        self._markers_on_screen = []

        # connect signals
        self._linelist_window.dismiss_linelists_window.connect(self._dismiss_linelists_window)
        self._linelist_window.erase_linelabels.connect(self._erase_linelabels)
        self._linelist_window.hub.plot_widget.mouse_enterexit.connect(self._handle_mouse_events)
        self._linelist_window.hub.plot_widget.sigRangeChanged.connect(self._handle_range_change)
        self._linelist_window.hub.plot_widget.sigRangeChanged.connect(
            lambda: self._handle_mouse_events(QEvent.Enter))

    # --------  Slots.

    # Buffering of zoom events.
    def _process_zoom_signal(self):
        if hasattr(self, '_zoom_markers_thread') and self._zoom_markers_thread:

            # for now, any object can be used as a zoom message.
            self._zoom_event_buffer._put(1)

    # These two slots below handle the logic associated with the
    # data_unit_changed and sigRangeChanged signals.

    def _handle_units_change(self):
        # we have to remove all line labels here, to prevent
        # the range re-calculation to include them when the
        # next sigRangeChanged signal is received.
        self._remove_linelabels_from_plot()
        self._units_changed = True

    def _handle_range_change(self):
        if self._units_changed:
            self._process_units_change()
            self._units_changed = False
        else:
            self._process_zoom_signal()

    # handle the re-plot of line labels after a plot units change.
    def _process_units_change(self):
        if hasattr(self, "_merged_linelist") and \
           hasattr(self, '_linelist_window') and \
           self._linelist_window:

            units = self._linelist_window.hub.plot_item.spectral_axis_unit

            self._merged_linelist[WAVELENGTH_COLUMN].convert_unit_to(units, equivalencies=u.spectral())
            self._merged_linelist[REDSHIFTED_WAVELENGTH_COLUMN].convert_unit_to(units, equivalencies=u.spectral())

            self._go_plot_markers(self._merged_linelist)

            # the plotted lines pane needs to be refreshed as well.
            self._linelist_window.erase_plotted_lines()
            self._linelist_window.display_plotted_lines(self._merged_linelist)

    def _dismiss_linelists_window(self, **kwargs):
        if self._linelist_window:
            self._erase_linelabels(self._plot_widget)
            self._linelist_window.dismiss()

    def _erase_linelabels(self, caller, *args, **kwargs):
        if caller != self._plot_widget:
            return

        if self._linelist_window:
            self._remove_linelabels_from_plot()
            self._linelist_window.erase_plotted_lines()

            self._destroy_zoom_markers_thread()

    # Main method for drawing line labels on the plot surface.
    def _plot_linelists(self, table_views, panes, units, caller, **kwargs):

        # If there is no valid plot item down to this point, then bail out (unfortunately)
        # because we cannot connect to the 'spectral_axis_unit_changed' signal.
        if self._linelist_window.hub.plot_item is None or \
            len(self._linelist_window.hub.visible_plot_items) == 0:
            message_box = QMessageBox()
            message_box.setText("No plot item selected.")
            message_box.setIcon(QMessageBox.Warning)
            message_box.setInformativeText(
                "There are currently no plot items selected. Please select "
                " plotted item before changing unit.")
            message_box.exec_()
            return

        # we have to postpone the 'spectral_axis_unit_changed' signal connection
        # to here. It cannot be done at constructor time because there is no valid
        # plot_item at that time.
        self._linelist_window.hub.plot_item.spectral_axis_unit_changed.connect(self._handle_units_change)

        # Get a list of the selected indices in each line list.
        # Build new line lists with only the selected rows.
        linelists_with_selections = []

        # Clear the plot surface of any line labels left
        # behind from previous draw action.
        self._remove_linelabels_from_plot()

        # Loop over every tabbed pane in the line lists window.
        for table_view, pane in zip(table_views, panes):
            line_list = pane.linelist

            # must map between view and underlying model
            # because of row sorting.
            selected_rows = table_view.selectionModel().selectedRows()
            model_selected_rows = []
            for sr in selected_rows:
                model_row = table_view.model().mapToSource(sr)
                model_selected_rows.append(model_row)

            new_list = line_list.extract_rows(model_selected_rows)

            # redshift correction for plotting the specific lines
            # defined in this list. Defined by the text content
            # and combo box setting.
            if pane.button_pane.redshift_textbox.hasAcceptableInput():
                redshift = float(pane.button_pane.redshift_textbox.text())
                z_units = pane.button_pane.combo_box_z_units.currentText()
                new_list.set_redshift(redshift, z_units)

            # color for plotting the specific lines defined in
            # this list, is defined by the itemData property.
            index = pane.button_pane.combo_box_color.currentIndex()
            color = pane.button_pane.combo_box_color.itemData(index, role=Qt.UserRole)
            new_list.set_color(color)

            # height for plotting the specific lines defined in
            # this list. Defined by the line edit text.
            if pane.button_pane.height_textbox.hasAcceptableInput():
                height = float(pane.button_pane.height_textbox.text())
                new_list.setHeight(height)

            linelists_with_selections.append(new_list)

        if len(linelists_with_selections) == 0:
            return

        # Merge all line lists into a single one.
        merged_linelist = LineList.merge(linelists_with_selections, units)

        # Finally, plot labels.
        self._go_plot_markers(merged_linelist)

        # Zooming the markers is a tricky business. On top of saving some plot
        # time by having the plot being de-cluttered at every zoom step, we
        # must control the rate at which the time-consuming zoom operation is
        # run, to prevent the app to become unresponsive. We use a threaded
        # mechanism to store zoom request events in a buffer, and then manage
        # its size, and the speed at which its contents get consumed.
        #
        # Notice that we can't use the dispatch mechanism to manage the zoom
        # thread and its signal-slot dependencies. Something in the dispatch
        # code messes up with the timing relationships in the GUI and secondary
        # threads, causing the “Timers cannot be started from another thread”
        # warning, and eventual app crash. We have to manage signals with explicit
        # code within the thread and in here.
        self._zoom_event_buffer = ZoomEventBuffer()
        self._zoom_markers_thread = ZoomMarkersThread(self, len(merged_linelist))
        self._zoom_markers_thread.do_zoom.connect(self._handle_zoom)

        # Populate the plotted lines pane in the line list window.
        if hasattr(self, '_linelist_window') and self._linelist_window:
            self._linelist_window.display_plotted_lines(merged_linelist)

        # The new line list just created becomes the default for
        # use in subsequent operations.
        self._merged_linelist = merged_linelist

    # Turns time-consuming processing in the zoom thread on/off when
    # mouse enter/leaves the plot. This enables other parts of the
    # app to retain their full computational speed when the mouse
    # pointer is outside the plot window.
    def _handle_mouse_events(self, event_type):
        if hasattr(self, '_zoom_markers_thread') and self._zoom_markers_thread:
            is_processing = self._zoom_markers_thread.is_processing

            # Detects when mouse entered the plot area but the thread is not processing yet.
            if event_type == QEvent.Enter and not is_processing:
                self._zoom_markers_thread._start_processing()
                return

            # Detects the complementary condition: mouse exited plot and thread still processing.
            if event_type == QEvent.Leave and is_processing:
                self._zoom_markers_thread._stop_processing()

#--------  Private methods.

    def _go_plot_markers(self, merged_linelist):
        # Code below is plotting all markers at a fixed height in
        # the screen coordinate system. Still TBD how to do this in
        # the generic case. Maybe derive heights from curve data
        # instead? Make the markers follow the curve ups and downs?
        #
        # Ideally we would like to have the marker's X coordinate
        # pinned down to the plot surface in data value, and the Y
        # coordinate pinned down in screen value. This would make
        # the markers to stay at the same height in the window even
        # when the plot is zoomed. The elegant nice way to do this
        # would be via the marker objects themselves to reposition
        # themselves on screen. This did not work though. There seems
        # to be a clash (maybe thread-related) in between the setPos
        # method and the auto-range facility in pyqtgraph.
        #
        # We managed to get the pinning in Y by brute force: remove
        # the markers and re-draw them in the new zoomed coordinates.
        # Note that it's not enough to remove a marker, reset its position,
        # and add it back to the plot. It's necessary to rebuild a new
        # marker instance. This probably has to do with the affine
        # transform objects that are stored inside each TextItem instance.
        # These transforms do not behave as expected when we run everything
        # with auto range turned on. Switching auto range on and off when
        # necessary does not work either.
        #
        # Profiling experiments showed that almost all the cost is spent inside
        # the pyqtgraph TextItem constructor. The total cost of this re-build
        # approach amounts to about 15-20% of the CPU time spent in zooming.
        # This is now being handled by a proxy instantiation mechanism. Profiling
        # experiments with the proxy mechanism in place show that the time taken
        # by the TextItem constructor drops to 4% of total CPU time.
        #
        # The pinning of the Y coordinate is handled by the handle_zoom method
        # that in turn relies in the storage of marker instances row-wise in the
        # line list table.

        # plot_widget = self._plot_widget.plotItem
        plot_widget = self._plot_widget

        height = self._compute_height(merged_linelist, plot_widget)

        # column names are defined in the YAML files
        # or by constants elsewhere.
        wave_column = merged_linelist.columns[REDSHIFTED_WAVELENGTH_COLUMN]
        id_column = merged_linelist.columns[ID_COLUMN]
        color_column = merged_linelist[COLOR_COLUMN]

        # To enable marker removal from plot, markers are stored
        # row-wise so as to match row selections in table views.
        markers = merged_linelist[MARKER_COLUMN]

        for row_index in range(len(wave_column)):

            # tool tip contains all info in table.
            tool_tip = ""
            for col_index in range(len(merged_linelist.columns)):
                col_name = merged_linelist.colnames[col_index]
                if not col_name in [COLOR_COLUMN]:
                    value = merged_linelist.columns[col_index][row_index]
                    tool_tip += col_name + '=' + str(value) + ', '

            # For now, use proxy markers to speed up processing.
            marker = LineIDMarkerProxy(wave_column[row_index],
                                       height[row_index],
                                       text=id_column[row_index],
                                       tip=tool_tip,
                                       color=color_column[row_index],
                                       orientation='vertical')
            markers[row_index] = marker

        # after all markers are created, check their positions
        # and disable some to de-clutter the plot.
        new_markers = self._declutter(markers)

        # place markers on screen
        for marker_proxy in new_markers:
            if marker_proxy:
                # build the real, full-fledged marker from proxy.
                real_marker = LineIDMarker(marker_proxy)
                real_marker.setPos(marker_proxy.x0, marker_proxy.y0)

                self._plot_widget.addItem(real_marker)
                self._markers_on_screen.append(real_marker)

        self._plot_widget.update()

    # Slot called by the zoom control thread.
    def _handle_zoom(self):
        # this method may be called by zoom signals that can be emitted
        # when a merged line list is not available yet.
        if hasattr(self, '_merged_linelist'):

            # Experiments with timing
            # self.Cron = QTime(0,0,0,0)
            # self.Cron.start()

            # update height column in line list based on
            # the new, zoomed coordinates.
            height_array = self._compute_height(self._merged_linelist, self._plot_widget)

            # remove markers that are displaying right now
            for index in range(len(self._markers_on_screen)):
                marker = self._markers_on_screen[index]
                self._plot_widget.removeItem(marker)
            self._markers_on_screen = []

            # update markers based on what is stored in the
            # marker_list table column.
            marker_list = self._merged_linelist[MARKER_COLUMN]
            for index in range(len(marker_list)):
                marker = marker_list[index]

                # New marker is built with same parameters as older marker that was
                # just removed, but for the new Y position.
                #
                # Note that it's not enough to remove a marker, reset its position,
                # and add it back to the plot. It's necessary to rebuild a new marker
                # instance. This probably has to do with the affine transform objects
                # that are stored inside each TextItem instance. These transforms do not
                # behave as expected when we run everything with auto range turned on.
                # Switching auto range on and off when necessary does not work either.
                #
                # Profiling experiments showed that almost all the cost is spent inside
                # the pyqtgraph TextItem constructor. The total cost of this re-build
                # approach amounts to about 15-20% of the CPU time spent in zooming.
                # This is now being handled by a proxy instantiation mechanism. Profiling
                # experiments with the proxy mechanism in place show that the time taken
                # by the TextItem constructor drops to 4% of total CPU time.

                new_marker = LineIDMarkerProxy(marker.x0, height_array[index], proxy=marker)

                # Replace old marker with new.
                marker_list[index] = new_marker

            # after all markers are created, check their relative positions
            # on screen and disable some to de-clutter the plot.
            decluttered_list = self._declutter(marker_list)

            # Finally, add the de-cluttered new markers to the plot.
            for marker_proxy in decluttered_list:
                if marker_proxy:
                    # build real, full-fledged marker from proxy.
                    real_marker = LineIDMarker(marker_proxy)
                    real_marker.setPos(real_marker.x0, real_marker.y0)

                    self._plot_widget.addItem(real_marker)
                    self._markers_on_screen.append(real_marker)

            self._plot_widget.update()

            # took = self.Cron.elapsed()
            # print("took: {0} msec" .format(str(took)))

            self._zoom_markers_thread.zoom_end.emit()

    # compute height to display each marker
    def _compute_height(self, merged_linelist, plot_widget):
        data_range = plot_widget.viewRange()
        ymin = data_range[1][0]
        ymax = data_range[1][1]

        return (ymax - ymin) * merged_linelist.columns[HEIGHT_COLUMN] + ymin

    # Returns a new list with proxy marker instances to be plotted.
    # This list is a (shallow) copy of the input list, where object
    # references are set to None whenever their distance in X+Y pixels
    # to the next neighbor is smaller than a given threshold.
    #
    # Using both X and Y as a distance criterion ensures that markers
    # displayed at different heights are not removed from the plot,
    # even when their X coordinate places them too close to each other.
    #
    # NOTE: However, using the sum of X and Y distances causes a lot more
    # markers to be displayed when separate data sets, both with large number
    # of lines, are displayed at different heights on screen. In a way, it
    # defeats the purpose of de-cluttering. And makes the code run slower:
    # right now, the CPU bottleneck is in the np.array() constructors that
    # build the X and Y arrays. Temporarily, we remove the Y array entirely.
    # In case this needs more work, users will give us feedback eventually.
    #
    # With these optimizations in place, about 7% of the CPU time spent
    # in zooming is due to the _declutter method. Almost all of it is in
    # line 341 (list comprehension + np.array() constructor).

    def _declutter(self, marker_list):
        if len(marker_list) > 10:
            threshold = 3

            data_range = self._plot_widget.viewRange()
            x_pixels = self._plot_widget.sceneBoundingRect().width()
            # y_pixels = self._plot_widget.sceneBoundingRect().height()  ###
            xmin = data_range[0][0]
            xmax = data_range[0][1]
            # ymin = data_range[1][0]  ###
            # ymax = data_range[1][1]  ###

            # compute X and Y distances in between markers, in screen pixels
            x = np.array([marker.x0 for marker in marker_list])
            xdist = np.abs(np.diff(x))
            xdist *= np.abs(x_pixels / (xmax - xmin))
            # y = np.array([marker.y0 for marker in marker_list])  ###
            # ydist = np.diff(y)                                   ###
            # ydist *= y_pixels / (ymax - ymin)                    ###

            # replace cluttered markers with None
            # new_array = np.where((xdist + ydist) < threshold, None, np.array(marker_list[1:]))     ####
            new_array = np.where(xdist < threshold, None, np.array(marker_list[1:]))

            # replace markers currently outside the wave range with None
            new_array_2 = np.where(x[1:] < xmin, None, new_array)
            new_array_3 = np.where(x[1:] > xmax, None, new_array_2)
            new_list = new_array_3.tolist()

            # make sure at least a few markers show
            if new_list.count(None) >= len(new_list) - 3:
                mid = int(len(new_list) / 2)
                mid_1 = int(max(0, mid - 8))
                mid_2 = int(min(mid + 8, len(new_list)-1))
                new_list[mid] = marker_list[mid]
                new_list[mid_1] = marker_list[mid_1]
                new_list[mid_2] = marker_list[mid_2]

            return new_list
        else:
            return marker_list

    def _remove_linelabels_from_plot(self):
        if hasattr(self, '_merged_linelist'):
            for index in range(len(self._markers_on_screen)):
                self._plot_widget.removeItem(self._markers_on_screen[index])
            self._plot_widget.update()
            self._markers_on_screen = []

    def _destroy_zoom_markers_thread(self):
        if hasattr(self, '_zoom_markers_thread') and self._zoom_markers_thread:
            self._zoom_markers_thread._stop_processing()
            self._zoom_markers_thread = None


class ZoomMarkersThread(QThread):
    """
    This class sets the pace to which zoom requests can be handled. It uses
    a mutex-lockable buffer to prevent piling up of too many zoom requests
    coming from cursor action on screen.

    Parameters
    ----------
    caller : :class:`~specviz.plugins.line_labels.line_labels_plotter.LineLabelsPlotter`
        The plotter instance that runs this thread..
    npoints : int
        The number of objects on screen to be zoomed (not used in this implementation).

    Attributes
    ----------
    do_zoom : Signal
        Signals that a zoom operation can be performed by the event loop.
    zoom_end : Signal
        Emitted by the event loop thread to signal that it is ready to
        receive another zoom request.
    """

    do_zoom = Signal()
    zoom_end = Signal()

    def __init__(self, caller, npoints):
        super(ZoomMarkersThread, self).__init__()
        self.buffer = caller._zoom_event_buffer
        self.npoints = npoints
        self.is_processing = False
        self.is_zooming = False

        self.zoom_end.connect(self._zoom_finished)

    def run(self):
        """
        Overrides the base class.
        """

        while(self.is_processing):

            value = self.buffer._get()
            if value:
                self.do_zoom.emit()

                self.is_zooming = True

                # wait for zoom to finish.
                while(self.is_zooming):
                    QThread.msleep(10)

            # one more, to prevent hiccups.
            QThread.msleep(10)

    def _zoom_finished(self):
        self.is_zooming = False

    def _start_processing(self):
        self.is_processing = True
        self.start()

    def _stop_processing(self):
        self.is_processing = False
        self.buffer._clear()


class ZoomEventBuffer(object):
    """
    A mutex-lockable buffer that stores zoom request events.

    """
    def __init__(self):
        self.buffer = []
        self.mutex = QMutex()

    def _clear(self):
        self.mutex.lock()
        self.buffer = []
        self.mutex.unlock()

    def _put(self, value):
        self.mutex.lock()

        # Don't let the buffer fill up too much.
        # Keep just the most recent zoom events.
        while len(self.buffer) > 5:
            self.buffer.pop()

        self.buffer.insert(0, value)

        self.mutex.unlock()

    def _get(self):
        self.mutex.lock()
        if len(self.buffer) > 0:
            value = self.buffer.pop()
        else:
            value = None
        self.mutex.unlock()
        return value
