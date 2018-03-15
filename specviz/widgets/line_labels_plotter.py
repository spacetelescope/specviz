import numpy as np

from qtpy.QtCore import QEvent, Qt, QThread, Signal, QMutex, QTime

from ..core.events import dispatch
from ..core.annotation import LineIDMarker, LineIDMarkerProxy
from ..core.linelist import LineList, \
    REDSHIFTED_WAVELENGTH_COLUMN, MARKER_COLUMN, ID_COLUMN, COLOR_COLUMN, HEIGHT_COLUMN


class LineLabelsPlotter(object):
    """
    Class that encapsulates and handles the gory details of line label
    plotting, and especially, zooming.
    """
    def __init__(self, caller, *args, **kwargs):
        super(LineLabelsPlotter, self).__init__(*args, **kwargs)

        # When porting code to this new class, we kept references
        # that explicitly point to objects in the caller code. A better
        # approach to encapsulation would be an improvement here.
        self._is_selected = caller.is_selected
        self._plot_item = caller.plot_item
        self._linelist_window = caller.linelist_window
        self._linelists = caller.linelists

        dispatch.setup(self)

    # Buffering of zoom events.
    def process_zoom_signal(self):
        if hasattr(self, '_zoom_markers_thread') and self._zoom_markers_thread:

            data_range = self._plot_item.viewRange()
            xmin = data_range[0][0]
            xmax = data_range[0][1]

            self._zoom_event_buffer.put((xmin, xmax))

#--------  Slots.

    @dispatch.register_listener("on_dismiss_linelists_window")
    def _dismiss_linelists_window(self, *args, **kwargs):
        if self._is_selected and self._linelist_window:
            self._linelist_window.hide()
            self._linelist_window = None

            self._destroy_zoom_markers_thread()

    @dispatch.register_listener("on_erase_linelabels")
    def _erase_linelabels(self, *args, **kwargs):
        if self._linelist_window and self._is_selected:
            self._destroy_zoom_markers_thread()

            self._remove_linelabels_from_plot()
            self._linelist_window.erasePlottedLines()

    @dispatch.register_listener("on_plot_linelists")
    def _plot_linelists(self, table_views, panes, units, **kwargs):

        if not self._is_selected:
            return

        # Get a list of the selected indices in each line list.
        # Build new line lists with only the selected rows.
        linelists_with_selections = []

        self._remove_linelabels_from_plot()

        for table_view, pane in zip(table_views, panes):
            # Find matching line list by its name. This could be made
            # simpler by the use of a dict. That breaks code elsewhere
            # though: it is assumed by that code that self.linelists
            # is a list and not a dict.
            view_name = table_view.model().getName()
            for k in range(len(self._linelists)):
                line_list = self._linelists[k]
                line_list_name = line_list.name

                if line_list_name == view_name:
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
                    if pane.redshift_textbox.hasAcceptableInput():
                        redshift = float(pane.redshift_textbox.text())
                        z_units = pane.combo_box_z_units.currentText()
                        new_list.setRedshift(redshift, z_units)

                    # color for plotting the specific lines defined in
                    # this list, is defined by the itemData property.
                    index = pane.combo_box_color.currentIndex()
                    color = pane.combo_box_color.itemData(index, role=Qt.UserRole)
                    new_list.setColor(color)

                    # height for plotting the specific lines defined in
                    # this list. Defined by the line edit text.
                    if pane.height_textbox.hasAcceptableInput():
                        height = float(pane.height_textbox.text())
                        new_list.setHeight(height)

                    linelists_with_selections.append(new_list)

        # Merge all line lists into a single one.
        merged_linelist = LineList.merge(linelists_with_selections, units)

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
        self._linelist_window.displayPlottedLines(merged_linelist)

        # The new line list just created becomes the default for
        # use in subsequent operations.
        self._merged_linelist = merged_linelist

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
        # approach amounts to about 10-12% of the elapsed time spent in zooming.
        #
        # The pinning of the Y coordinate is handled by the handle_zoom
        # method that in turn relies in the storage of marker instances
        # row-wise in the line list table.
        plot_item = self._plot_item

        height = self._compute_height(merged_linelist, plot_item)

        # column names are defined in the YAML files
        # or by constants elsewhere.
        wave_column = merged_linelist.columns[REDSHIFTED_WAVELENGTH_COLUMN]
        id_column = merged_linelist.columns[ID_COLUMN]
        color_column = merged_linelist[COLOR_COLUMN]

        # To enable marker removal from plot, markers are stored
        # row-wise so as to match row selections in table views.
        marker_column = merged_linelist[MARKER_COLUMN]

        for row_index in range(len(wave_column)):

            # tool tip contains all info in table.
            tool_tip = ""
            for col_index in range(len(merged_linelist.columns)):
                col_name = merged_linelist.colnames[col_index]
                if not col_name in [COLOR_COLUMN]:
                    value = merged_linelist.columns[col_index][row_index]
                    tool_tip += col_name + '=' + str(value) + ', '

            marker = LineIDMarker(text=id_column[row_index],
                                  plot_item=plot_item,
                                  tip=tool_tip,
                                  color=color_column[row_index],
                                  orientation='vertical')

            marker.setPos(wave_column[row_index], height[row_index])

            marker_column[row_index] = marker

        # after all markers are created, check their positions
        # and disable some to de-clutter the plot.
        new_column = self._declutter(marker_column)
        for marker in new_column:
            if marker:
                self._plot_item.addItem(marker)

        plot_item.update()

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
            height_array = self._compute_height(self._merged_linelist, self._plot_item)

            # update markers based on what is stored in the
            # marker_list table column.
            marker_list = self._merged_linelist[MARKER_COLUMN]
            for index in range(len(marker_list)):
                marker = marker_list[index]

                self._plot_item.removeItem(marker)

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
                # approach amounts to about 10-12% of the elapsed time spent in zooming.

                new_marker = LineIDMarker(marker=marker)
                new_marker.setPos(marker.x(), height_array[index])

                # Replace old marker with new.
                marker_list[index] = new_marker

            # after all markers are created, check their relative
            # positions on screen and disable some to de-clutter
            # the plot.
            decluttered_list = self._declutter(marker_list)

            # Finally, add the de-cluttered new markers to the plot.
            for marker in decluttered_list:
                if marker:
                    self._plot_item.addItem(marker)

            self._plot_item.update()

            # took = self.Cron.elapsed()
            # print("took: {0} msec" .format(str(took)))

            self._zoom_markers_thread.zoom_end.emit()

    # compute height to display each marker
    def _compute_height(self, merged_linelist, plot_item):
        data_range = plot_item.viewRange()
        ymin = data_range[1][0]
        ymax = data_range[1][1]

        return (ymax - ymin) * merged_linelist.columns[HEIGHT_COLUMN] + ymin

    # Returns a new list with marker instances to be plotted.
    # This list is a (shallow) copy of the input list, where
    # objects references are set to None whenever their distance
    # in X+Y pixels to the next neighbor is smaller than a given
    # threshold. Using both X and Y as a distance criterion
    # ensures that markers displayed at different heights are
    # not removed from the plot, even when their X coordinate
    # places them too close to each other.
    def _declutter(self, marker_list):
        if len(marker_list) > 10:
            threshold = 5

            data_range = self._plot_item.viewRange()
            x_pixels = self._plot_item.sceneBoundingRect().width()
            y_pixels = self._plot_item.sceneBoundingRect().height()
            xmin = data_range[0][0]
            xmax = data_range[0][1]
            ymin = data_range[1][0]
            ymax = data_range[1][1]

            # compute X and Y distances in between markers, in screen pixels
            x = np.array([marker.x() for marker in marker_list])
            xdist = np.diff(x)
            xdist *= x_pixels / (xmax - xmin)
            y = np.array([marker.y() for marker in marker_list])
            ydist = np.diff(y)
            ydist *= y_pixels / (ymax - ymin)

            # replace cluttered markers with None
            new_array = np.where((xdist + ydist) < threshold, None, np.array(marker_list[1:]))

            # replace markers currently outside the wave range with None
            new_array_2 = np.where(x[1:] < xmin, None, new_array)
            new_array_3 = np.where(x[1:] > xmax, None, new_array_2)
            new_list = new_array_3.tolist()

            # make sure at least one marker shows
            if new_list.count(None) == len(new_list):
                new_list[0] = marker_list[0]

            return new_list
        else:
            return marker_list

    @dispatch.register_listener("mouse_enterexit")
    def _handle_mouse_events(self, event_type):
        # Turns time-consuming processing in the zoom thread on/off when
        # mouse enter/leaves the plot. This enables that other parts of
        # the app retain their full computational speed when the mouse
        # pointer is outside the plot window.
        if hasattr(self, '_zoom_markers_thread') and self._zoom_markers_thread:
            is_processing = self._zoom_markers_thread.is_processing

            # Detects when mouse entered the plot area but the thread is not processing yet.
            if event_type == QEvent.Enter and not is_processing:
                self._zoom_markers_thread.start_processing()
                return

            # Detects the complementary condition: mouse exited plot and thread still processing.
            if event_type == QEvent.Leave and is_processing:
                self._zoom_markers_thread.stop_processing()

    def _remove_linelabels_from_plot(self):
        if hasattr(self, '_merged_linelist'):
            marker_column = self._merged_linelist[MARKER_COLUMN]
            for index in range(len(marker_column)):
                self._plot_item.removeItem(marker_column[index])
            self._plot_item.update()

    def _destroy_zoom_markers_thread(self):
        if hasattr(self, '_zoom_markers_thread') and self._zoom_markers_thread:
            self._zoom_markers_thread.stop_processing()
            self._zoom_markers_thread = None


class ZoomMarkersThread(QThread):

    # Notice that we can't use the dispatch mechanism to manage the zoom
    # thread and its signal-slot dependencies. Something in the dispatch
    # code messes up with the timing relationships in the GUI and secondary
    # threads, causing the “Timers cannot be started from another thread”
    # warning, and eventual app crash. We have to manage locally-defined
    # signals instead, explicitly connecting them with their slots

    do_zoom = Signal()
    zoom_end = Signal()

    def __init__(self, caller, npoints):
        super(ZoomMarkersThread, self).__init__()
        self.buffer = caller._zoom_event_buffer
        self.npoints = npoints
        self.is_processing = False
        self.is_zooming = False

        self.zoom_end.connect(self.zoom_finished)

    def run(self):
        while(self.is_processing):

            value = self.buffer.get()
            if value:
                self.do_zoom.emit()

                self.is_zooming = True

                # wait for zoom to finish.
                while(self.is_zooming):
                    QThread.msleep(10)

            # one more, to prevent hiccups.
            QThread.msleep(10)

    def zoom_finished(self):
        self.is_zooming = False

    def start_processing(self):
        self.is_processing = True
        self.start()

    def stop_processing(self):
        self.is_processing = False
        self.buffer.clear()


class ZoomEventBuffer(object):

    # A mutex-lockable buffer that stores zoom request events.

    def __init__(self):
        self.buffer = []
        self.mutex = QMutex()

    def clear(self):
        self.mutex.lock()
        self.buffer = []
        self.mutex.unlock()

    def put(self, value):
        self.mutex.lock()

        # Don't let the buffer fill up too much.
        # Keep just the most recent zoom events.
        while len(self.buffer) > 2:
            self.buffer.pop()

        self.buffer.insert(0, value)

        self.mutex.unlock()

    def get(self):
        self.mutex.lock()
        if len(self.buffer) > 0:
            value = self.buffer.pop()
        else:
            value = None
        self.mutex.unlock()
        return value