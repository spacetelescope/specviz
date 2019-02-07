"""
Define all the line list-based windows and dialogs
"""
import os
import sys

from qtpy.QtWidgets import (QWidget, QTabWidget, QVBoxLayout, QTabBar,
                            QTableView, QMainWindow, QAbstractItemView, QStackedLayout,
                            QLayout, QGridLayout, QBoxLayout, QTextBrowser, QComboBox,
                            QDialog, QErrorMessage, QSizePolicy)
from qtpy.QtGui import QColor, QStandardItem, QDoubleValidator, QFont, QIcon
from qtpy.QtCore import (Qt, Signal, QAbstractTableModel, QVariant, QSortFilterProxyModel)
from qtpy import compat
from qtpy.uic import loadUi

import pyqtgraph as pg

from astropy import units as u
from astropy.units import Quantity
from astropy.units.core import UnitConversionError
from astropy.io import ascii

from ...core.plugin import plugin

from . import linelist
from .linelist import WAVELENGTH_COLUMN, ERROR_COLUMN, DEFAULT_HEIGHT
from .linelist import columns_to_remove
from .line_labels_plotter import LineLabelsPlotter

__all__ = ['LineListsPlugin', 'LineListsWindow', 'LineListPane', 'PlottedLinesPane', 'LineListTableModel', 'SortModel']


# We need our own mapping because the list with color names returned by
# QColor.colorNames() is inconsistent with the color names in Qt.GlobalColor.
ID_COLORS = {
    'black':      Qt.black,
    'red':        Qt.red,
    'green':      Qt.green,
    'blue':       Qt.blue,
    'cyan':       Qt.cyan,
    'magenta':    Qt.magenta,
    'dark red':   Qt.darkRed,
    'dark green': Qt.darkGreen,
    'dark blue':  Qt.darkBlue
}

PLOTTED = "Plotted"
NLINES_WARN = 150

# Commonly used spectral axis units have custom formats
# for displaying values in the dialog text fields.
units_formats = {
    "Angstrom": "%.2f",
    "micron": "%.4f",
    "cm": "%.4g",
    "m": "%.4g",
    "Hz": "%.4g",
    "eV": "%.3f"
}

# Function that creates one single tabbed pane with one single view of a line list.

def _create_line_list_pane(linelist, table_model, caller):

    table_view = QTableView()

    # disabling sorting will significantly speed up the rendering,
    # in particular of large line lists. These lists are often jumbled
    # in wavelength, and consequently difficult to read and use, so
    # having a sorting option is useful indeed. It remains to be seen
    # what would be the approach users will favor. We might add a toggle
    # that users can set/reset depending on their preferences.
    table_view.setSortingEnabled(False)
    sort_proxy = SortModel(table_model.get_name())
    sort_proxy.setSourceModel(table_model)

    table_view.setModel(sort_proxy)
    table_view.setSortingEnabled(True)
    table_view.horizontalHeader().setStretchLastSection(True)

    # playing with these doesn't speed up the sorting, regardless of whatever
    # you may read on the net.
    #
    # table_view.horizontalHeader().setResizeMode(QHeaderView.Fixed)
    # table_view.verticalHeader().setResizeMode(QHeaderView.Fixed)
    # table_view.horizontalHeader().setStretchLastSection(False)
    # table_view.verticalHeader().setStretchLastSection(False)
    table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
    table_view.resizeColumnsToContents()

    # this preserves the original sorting state of the list. Use zero
    # to sort by wavelength on load. Doesn't seem to affect performance
    # by much tough.
    sort_proxy.sort(-1, Qt.AscendingOrder)

    # table selections will change the total count of lines selected.
    pane = LineListPane(table_view, linelist, sort_proxy, caller)

    return pane, table_view

# line list widget storage.
linelists_windows = {}

@plugin.plugin_bar("Line labels", icon=QIcon(":/icons/price.svg"))
class LineListsPlugin(QWidget):
    """
    Top class for the line labels plugin. This is the class that handles
    the line lists window, where the user manages and interacts with the
    line lists.

    This class acts as a interface adapter of sorts for the actual class
    that does the work, LineListsWindow.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        panel_layout = QStackedLayout()
        panel_layout.setSizeConstraint(QLayout.SetMaximumSize)
        panel_layout.setContentsMargins (0,0,0,0)
        self.setLayout(panel_layout)

        # cache the line lists for speedier access
        linelist.populate_linelists_cache()

        self.hub.workspace.mdi_area.subWindowActivated.connect(self._plot_selected)

    # line list widgets for the plugin bar are associated with their corresponding
    # plot widget via a key built from the plot widget instance hash. References are
    # kept in a dict for management purposes, but the actual widgets are kept in a
    # stacked layout. This method provides the logic to select the appropriate line
    # list widget and display it, upon selection of the subwindow that contains the
    # plot widget.
    def _plot_selected(self):
        if hasattr(self.hub, "plot_widget") and self.hub.plot_widget:
            key = self.hub.plot_widget.__hash__()
            if key not in linelists_windows:
                # build a new line list window and display it.
                linelists_windows[key] = LineListsWindow(self.hub, parent=self)

                self.layout().addWidget(linelists_windows[key])
                self.layout().setCurrentIndex(self.layout().count()-1)

            else:
                # re-display an existing line list window.
                index = self.layout().indexOf(linelists_windows[key])
                self.layout().setCurrentIndex(index)

class LineListsWindow(QWidget):
    """
    The actual line lists widget.

    Parameters
    ----------
    hub : :class:`~specviz.core.Hub`
        The Hub object for the plugin.

    Signals
    -------
    erase_linelabels : Signal
        Fired when a line list is removed by user action.
    dismiss_linelists_window : Signal
        Fired when the entire widget is dismissed. This happens only
        when the corresponding plot widget is dismissed by user action.
    """

    erase_linelabels = Signal(pg.PlotWidget)
    dismiss_linelists_window = Signal()

    def __init__(self, hub, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hub = hub

        self.wave_range = (None, None)

        loadUi(os.path.join(os.path.dirname(__file__), "ui", "linelists_window.ui"), self)

        # QtDesigner can't add a combo box to a tool bar...
        self.line_list_selector = QComboBox()
        self.line_list_selector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.line_list_selector.setMinimumWidth(230)
        self.line_list_selector.setToolTip("Select line list from internal library")
        self.main_toolbar.addWidget(self.line_list_selector)

        # QtDesigner creates tabbed widgets with 2 tabs, and doesn't allow
        # removing then in the designer itself. Remove in here then.
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)

        # Local references for often used objects.
        self.plot_window = self.hub.plot_window

        # Request that line lists be read from wherever are they sources.
        if not hasattr(self, 'linelists'):
            self._request_linelists()

            # Populate line list selector with internal line lists
            model = self.line_list_selector.model()
            item = QStandardItem("Select line list")
            font = QFont("Monospace")
            font.setStyleHint(QFont.TypeWriter)
            font.setPointSize(12)
            item.setFont(font)
            model.appendRow(item)
            for description in linelist.descriptions():
                item = QStandardItem(str(description))
                item.setFont(font)
                model.appendRow(item)

        self.line_labels_plotter = LineLabelsPlotter(self)

        # Connect controls to appropriate signals.

        self.draw_button.clicked.connect(
            lambda:self.line_labels_plotter._plot_linelists(
            table_views=self._get_table_views(),
            panes=self._get_panes(),
            units=self.hub.plot_widget.spectral_axis_unit,
            caller=self.line_labels_plotter))

        self.erase_button.clicked.connect(lambda:self.erase_linelabels.emit(self.plot_window.plot_widget))
        self.dismiss_button.clicked.connect(self.dismiss_linelists_window.emit)

        self.actionOpen.triggered.connect(lambda:self._open_linelist_file(file_name=None))
        self.actionExport.triggered.connect(lambda:self._export_to_file(file_name=None))
        self.line_list_selector.currentIndexChanged.connect(self._lineList_selection_change)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close)

        self.hub.plot_window.window_removed.connect(self.dismiss_linelists_window.emit)

    def dismiss(self):
        """
        The Dismiss button just clears the plug-in
        window from whatever line lists it's holding.
        """
        v = self.tab_widget.count()
        for index in range(v-1,-1,-1):
            self.tab_widget.removeTab(index)

    def _get_waverange_from_dialog(self, line_list):
        # there is a widget-wide wavelength range so as to preserve
        # the user definition from call to call. At the initial
        # call, the wave range is initialized with whatever range
        # is being displayed in the spectrum plot window.
        if self.wave_range[0] == None or self.wave_range[1] == None:
            self.wave_range = self._find_wavelength_range()

        wrange = self._build_waverange_dialog(self.wave_range, line_list)

        self.wave_range = wrange

    def _lineList_selection_change(self, index):
        # ignore first element in drop down. It contains
        # the "Select line list" message.
        if index > 0 and hasattr(self.hub, 'plot_widget') and self.hub.plot_widget.spectral_axis_unit:
            line_list = linelist.get_from_cache(index - 1)

            try:
                self._get_waverange_from_dialog(line_list)
                if self.wave_range[0] and self.wave_range[1]:
                    self._build_view(line_list, 0, waverange=self.wave_range)

                self.line_list_selector.setCurrentIndex(0)

            except UnitConversionError as err:
                error_dialog = QErrorMessage()
                error_dialog.showMessage('Units conversion not possible.')
                error_dialog.exec_()

    def _build_waverange_dialog(self, wave_range, line_list):

        dialog = QDialog()

        loadUi(os.path.join(os.path.dirname(__file__), "ui", "linelists_waverange.ui"), dialog)

        # convert from line list native units to whatever units
        # are currently being displayed in the spectral axis.
        linelist_units = wave_range[0].unit
        spectral_axis_unit = self.hub.plot_widget.spectral_axis_unit
        w0 = wave_range[0].to(spectral_axis_unit, equivalencies=u.spectral())
        w1 = wave_range[1].to(spectral_axis_unit, equivalencies=u.spectral())

        # populate labels with correct physical quantity name
        dispersion_unit = u.Unit(spectral_axis_unit or "")
        if dispersion_unit.physical_type == 'length':
            dialog.minwave_label.setText("Minimum wavelength")
            dialog.maxwave_label.setText("Maximum wavelength")
        elif dispersion_unit.physical_type == 'frequency':
            dialog.minwave_label.setText("Minimum frequency")
            dialog.maxwave_label.setText("Maximum frequency")
        elif dispersion_unit.physical_type == 'energy':
            dialog.minwave_label.setText("Minimum energy")
            dialog.maxwave_label.setText("Maximum energy")
        else:
            dialog.minwave_label.setText("Minimum disp. var.")
            dialog.maxwave_label.setText("Maximum disp. var.")

        # pick a good format to display values represented
        # in the currently selected plot units.
        if str(w0.unit) in units_formats:
            fmt = units_formats[str(w0.unit)]
        else:
            # use generic formatting for weirder units
            fmt = "%.6g"

        dialog.min_text.setText(fmt % w0.value)
        dialog.max_text.setText(fmt % w1.value)

        validator = QDoubleValidator()
        validator.setBottom(0.0)
        dialog.min_text.setValidator(validator)
        dialog.max_text.setValidator(validator)

        dialog.nlines_label = self._compute_nlines_in_waverange(line_list, dialog.min_text, dialog.max_text,
                                                                dialog.nlines_label, linelist_units, spectral_axis_unit)

        dialog.min_text.editingFinished.connect(lambda: self._compute_nlines_in_waverange(line_list,
                                                                                          dialog.min_text,
                                                                                          dialog.max_text,
                                                                                          dialog.nlines_label,
                                                                                          linelist_units,
                                                                                          spectral_axis_unit))
        dialog.max_text.editingFinished.connect(lambda: self._compute_nlines_in_waverange(line_list,
                                                                                          dialog.min_text,
                                                                                          dialog.max_text,
                                                                                          dialog.nlines_label,
                                                                                          linelist_units,
                                                                                          spectral_axis_unit))
        accepted = dialog.exec_() > 0

        amin = amax = None
        if accepted:
            return self._get_range_from_textfields(dialog.min_text, dialog.max_text,
                                                   linelist_units, spectral_axis_unit)
        return (amin, amax)

    def _get_range_from_textfields(self, min_text, max_text, linelist_units, plot_units):
        amin = amax = None
        if min_text.hasAcceptableInput() and max_text.hasAcceptableInput():

            amin = float(min_text.text())
            amax = float(max_text.text())

            amin = Quantity(amin, plot_units)
            amax = Quantity(amax, plot_units)

            amin = amin.to(linelist_units, equivalencies=u.spectral())
            amax = amax.to(linelist_units, equivalencies=u.spectral())

        return (amin, amax)

    # computes how many lines in the supplied list
    # fall within the supplied wavelength range. The
    # result populates the supplied label. Or, it
    # builds a fresh QLabel with the result.
    def _compute_nlines_in_waverange(self, line_list, min_text, max_text, label,
                                     linelist_units, plot_units):

        amin, amax = self._get_range_from_textfields(min_text, max_text, linelist_units, plot_units)

        if amin != None or amax != None:
            r = (amin, amax)

            extracted = line_list.extract_range(r)
            nlines = len(extracted[WAVELENGTH_COLUMN].data)

            label.setText(str(nlines))
            color = 'black' if nlines < NLINES_WARN else 'red'
            label.setStyleSheet('color:' + color)

        return label

    def _build_view(self, line_list, index, waverange=(None, None)):

        if self.wave_range[0] and self.wave_range[1]:
            line_list = line_list.extract_range(waverange)

        table_model = LineListTableModel(line_list)

        if table_model.rowCount() > 0:
            # here we add the first pane (the one with the entire
            # original line list), to the tabbed pane that contains
            # the line sets corresponding to the current line list.
            lineset_tabbed_pane = QTabWidget()
            lineset_tabbed_pane.setTabsClosable(True)

            pane, table_view = _create_line_list_pane(line_list, table_model, self)
            lineset_tabbed_pane.addTab(pane, "Original")
            pane._set_line_sets_tabbed_pane(lineset_tabbed_pane)

            table_view.selectionModel().selectionChanged.connect(pane._handle_button_activation)

            # internal signals do not use Hub infrastructure.
            table_view.selectionModel().selectionChanged.connect(self._count_selections)

            # now we add this "line set tabbed pane" to the main tabbed
            # pane, with name taken from the list model.
            self.tab_widget.insertTab(index, lineset_tabbed_pane, table_model.get_name())
            self.tab_widget.setCurrentIndex(index)

            # store for use down stream.
            # self.table_views.append(table_view)
            # self.set_tabbed_panes.append(set_tabbed_pane)
            # self.tab_count.append(0)
            # self.panes.append(pane)

            return line_list

    def _build_views(self, plot_window):
        window_linelists = plot_window.linelists
        for linelist, index in zip(window_linelists, range(len(window_linelists))):
            self._build_view(linelist, index)

        # add extra tab to hold the plotted lines view.
        widget_count = self.tab_widget.count()
        if widget_count > 0:
            self.tab_widget.addTab(QWidget(), PLOTTED)
            self.tab_widget.tabBar().setTabButton(widget_count - 1, QTabBar.LeftSide, None)

    def _get_panes(self):
        result = []
        for index_1 in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(index_1)
            if isinstance(widget, QTabWidget) and self.tab_widget.tabText(index_1) != PLOTTED:
                # do not use list comprehension here!
                for index_2 in range(widget.count()):
                    result.append(widget.widget(index_2))
        return result

    def _request_linelists(self):
        self.waverange = self._find_wavelength_range()

        self.linelists = linelist.ingest(self.waverange)

    def _find_wavelength_range(self):
        unit = self.hub.plot_widget.spectral_axis_unit
        data_item_list = self.hub.plot_widget.plotItem.dataItems

        amin = sys.float_info.max
        amax = -amin
        for item in data_item_list:
            value = item.dataBounds(0)
            amin = min(value[0], amin)
            amax = max(value[1], amax)
        amin = Quantity(amin, unit)
        amax = Quantity(amax, unit)

        return (amin, amax)

    # computes total of rows selected in all table views in all panes
    # and displays result in GUI.
    def _count_selections(self):
        panes = self._get_panes()
        sizes = [len(pane.table_view.selectionModel().selectedRows()) for pane in panes]
        import functools
        count = functools.reduce(lambda x, y: x + y, sizes)

        # display total selected rows, with eventual warning.
        self.lines_selected_label.setText(str(count))
        color = 'black' if count < NLINES_WARN else 'red'
        self.lines_selected_label.setStyleSheet('color:' + color)

        self.lines_selected_label.repaint()

    def _on_tab_close(self, index):
        self.tab_widget.removeTab(index)

    def _open_linelist_file(self, file_name=None):
        if file_name is None:

            filters = ['Line list (*.yaml *.ecsv)']
            file_name, _file_filter = compat.getopenfilenames(filters=";;".join(filters))

            # For now, lets assume both the line list itself, and its
            # associated YAML descriptor file, live in the same directory.
            # Not an issue for self-contained ecsv files.
            if file_name is not None and len(file_name) > 0:
                name = file_name[0]
                line_list = linelist.get_from_file(os.path.dirname(name), name)

                if line_list:
                    self._get_waverange_from_dialog(line_list)
                    if self.wave_range[0] and self.wave_range[1]:
                        line_list = self._build_view(line_list, 0, waverange=self.wave_range)

                        if not hasattr(self.plot_window, 'linelists'):
                            self.plot_window.linelists = []

                        self.plot_window.linelists.append(line_list)

    def _export_to_file(self, file_name=None):
        if file_name is None:

            if hasattr(self, '_plotted_lines_pane') and self._plotted_lines_pane:

                filters = ['Line list (*.ecsv)']
                file_name, _file_filter = compat.getsavefilename(filters=";;".join(filters))

                if not file_name.endswith('.ecsv'):
                    file_name += '.ecsv'

                output_table = self._plotted_lines_pane.plotted_lines.table

                for colum_name in columns_to_remove:
                    if colum_name in output_table.colnames:
                        output_table.remove_column(colum_name)

                ascii.write(output_table, output=file_name, format='ecsv')

    def display_plotted_lines(self, linelist):
        """
        Displays the input line list in the plotted
        lines tabbed pane.

        Parameters
        ----------
        linelist: LineList
            The line list to display in the plotted lines tabbed pane
        """
        self._plotted_lines_pane = PlottedLinesPane(linelist)

        for index in range(self.tab_widget.count()):
            tab_text = self.tab_widget.tabText(index)
            if tab_text == PLOTTED:
                self.tab_widget.removeTab(index)
                self.tab_widget.insertTab(index, self._plotted_lines_pane, PLOTTED)
                return

        # if no plotted pane yet, create one.
        index = self.tab_widget.count()
        self.tab_widget.insertTab(index, self._plotted_lines_pane, PLOTTED)

    def erase_plotted_lines(self):
        """
        Removes the plotted lines tabbed pane.

        Called in response for the Erase button.
        """
        for index in range(self.tab_widget.count()):
            tab_text = self.tab_widget.tabText(index)
            if tab_text == PLOTTED:
                self.tab_widget.removeTab(index)

    # Returns a flat rendering of the panes and table views stored
    # in the two-tiered tabbed window. These flat renderings are
    # required by the drawing code.
    def _get_table_views(self):
        panes = self._get_panes()
        return [pane.table_view for pane in panes]


class LineListPane(QWidget):
    """
    Class that manages a single pane dedicated to a single list.

    Parameters
    ----------
    table_view : :class:`QTableView`
        The table view corresponding to the line list.
    linelist : :class:`~specviz.plugins.line_labels.linelist.LineList`
        The line list.
    sort_proxy : :class:`~specviz.plugins.line_labels.linelist_window.SortModel`
        The table model with sorting capabilities.
    caller :  :class:`~specviz.plugins.line_labels.linelist_window.LineListsWindow`
        The caller.
    """

    def __init__(self, table_view, linelist, sort_proxy, caller, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

        self.table_view = table_view
        self.linelist = linelist
        self._sort_proxy = sort_proxy
        self._caller = caller

        self._build_GUI(linelist, table_view)

    def _build_GUI(self, linelist, table_view):
        panel_layout = QGridLayout()
        panel_layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.setLayout(panel_layout)

        # GUI cannot be completely defined in a .ui file.
        # It has to be built on-the-fly here.
        self.button_pane = QWidget()
        loadUi(os.path.join(os.path.dirname(__file__), "ui", "linelists_panel_buttons.ui"), self.button_pane)

        # internal signals do not use Hub infrastructure.
        self.button_pane.create_set_button.clicked.connect(self._create_set)
        self.button_pane.deselect_button.clicked.connect(table_view.clearSelection)

        # header with line list metadata.
        info = QTextBrowser()
        info.setMaximumHeight(100)
        info.setAutoFillBackground(True)
        info.setStyleSheet("background-color: rgb(230,230,230);")
        for comment in linelist.meta['comments']:
            info.append(comment)

        # populate color picker
        model = self.button_pane.combo_box_color.model()
        for cname in ID_COLORS:
            item = QStandardItem(cname)
            item.setForeground(ID_COLORS[cname])
            item.setData(QColor(ID_COLORS[cname]), role=Qt.UserRole)
            model.appendRow(item)

        # set validators
        validator = QDoubleValidator()
        validator.setRange(0.05, 0.95, decimals=2)
        self.button_pane.height_textbox.setValidator(validator)
        validator = QDoubleValidator()
        validator.setRange(-1.e5, 1.e10, decimals=4)
        self.button_pane.redshift_textbox.setValidator(validator)

        model = self.button_pane.combo_box_z_units.model()
        for uname in ['z', 'km/s']:
            item = QStandardItem(uname)
            model.appendRow(item)

        # put it all together
        panel_layout.addWidget(info,0,0)
        panel_layout.addWidget(table_view,1,0)
        panel_layout.addWidget(self.button_pane,2,0)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def _set_line_sets_tabbed_pane(self, pane):
        self._sets_tabbed_pane = pane

        # this must be set only once per tabbed pane, otherwise multiple
        # signal handlers can result in more than one tab being closed
        # when just one closing request is posted. Internal signals do
        # not use Hub infrastructure.
        self._sets_tabbed_pane.tabCloseRequested.connect(self._tab_close)

    def _create_set(self):
        # build list with only the selected rows. These must be model
        # rows, not view rows!
        selected_view_rows = self.table_view.selectionModel().selectedRows()
        selected_model_rows = [self._sort_proxy.mapToSource(x) for x in selected_view_rows]

        if len(selected_model_rows) > 0:
            r = [x for x in selected_model_rows]
            local_list = self.linelist.extract_rows(r)

            # name is used to match lists with table views
            local_list.name = self.linelist.name

            table_model = LineListTableModel(local_list)
            pane, table_view = _create_line_list_pane(local_list, table_model, self._caller)

            pane._sets_tabbed_pane = self._sets_tabbed_pane
            # Internal signals do not use Hub infrastructure.
            table_view.selectionModel().selectionChanged.connect(self._caller._count_selections)

            table_view.selectionModel().selectionChanged.connect(pane._handle_button_activation)

            self._sets_tabbed_pane.addTab(pane, str(self._sets_tabbed_pane.count()))

    def _tab_close(self, index):
        self._sets_tabbed_pane.removeTab(index)

    def _handle_button_activation(self):
        nselected = len(self.table_view.selectionModel().selectedRows())
        self.button_pane.create_set_button.setEnabled(nselected > 0)


class PlottedLinesPane(QWidget):
    """
    This holds the list with the currently plotted lines.

    Parameters
    ----------
    linelist : :class:`~specviz.plugins.line_labels.linelist.LineList`
        The line list containing only the labels actually plotted.

    """
    # This view is re-built every time a new set of markers
    # is plotted. The list view build here ends up being the
    # main bottleneck in terms of execution time perceived by
    # the user (found this using cProfile). The time to build
    # the list is about the same as the time spent in the
    # paint() methods of all components in the plot, for a set
    # of a couple hundred markers. Most of that time in turn is
    # spent in the column resizing method in the table view. If
    # sorting is enabled for this view, times will increase
    # dramatically.
    #
    # This plotted lines pane represents one of the possible
    # implementations of the last requirement in Tony Marston's
    # line list document (option to show line information for
    # lines shown in the plot). Given the slowness of it, it
    # would be good to have feedback on this in order to try
    # alternate implementation approaches (a simple ASCII table
    # might suffice, perhaps). An alternate approach would be to
    # use some timing algorithm that will prevent the view to be
    # rebuilt rigth after a previous rebuilt. A time delay of sorts
    # could take care of that.

    def __init__(self, plotted_lines, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

        self.plotted_lines = plotted_lines

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.setLayout(layout)

        table_model = LineListTableModel(plotted_lines)
        if table_model.rowCount() > 0:
            table_view = QTableView()

            # disabling sorting will significantly speed up theWidget
            # plot. This is because the table view must be re-built
            # every time a new set of markers is drawn on the plot
            # surface. Alternate approaches are worth examining. It
            # remains to be seen what would be the approach users
            # will favor.

            table_view.setSortingEnabled(False)
            proxy = SortModel(table_model.get_name())
            proxy.setSourceModel(table_model)
            table_view.setModel(proxy)
            table_view.setSortingEnabled(True)

            table_view.setSelectionMode(QAbstractItemView.NoSelection)
            table_view.horizontalHeader().setStretchLastSection(True)
            table_view.resizeColumnsToContents()

            layout.addWidget(table_view)


class LineListTableModel(QAbstractTableModel):
    """
    The line list table model.

    Parameters
    ----------
    linelist : :class:`~specviz.plugins.line_labels.linelist.LineList`
        The line list.

    """

    def __init__(self, linelist, parent=None, *args):

        QAbstractTableModel.__init__(self, parent, *args)

        self._linelist = linelist

        #TODO move entire table contents to an array of QVector
        # instances that will store the columns. This should
        # speed up the sorting (as far as some indications in
        # the net suggest:
        # http://www.qtforum.org/article/30638/qsortfilterproxymodel-qtreeview-sort-performance.html).
        # Bummer... this is C++ only; PyQt never went to the trouble
        # of converting QVector to python.
        #
        # get rid entirely of astropy table and store its contents in
        # a 2-D list of lists. By using python lists instead of an
        # astropy table, and storing the QVariant instances instead
        # of the raw content, we can speed up sorting by a factor > 10X.

        # we have to do this here because some lists may
        # have no lines at all.
        self._nrows = 0
        self._ncols = 0

        self._row_cells = []

        for row in self._linelist:
            cells = []
            for rindex in range(len(row)):
                cell = row[rindex]

                # handling of a color object can be tricky. Color names
                # returned by QColor.colorNames() are inconsistent with
                # color names in Qt.GlobalColor. We just go to the basics
                # and compare color equality (or closeness) using a distance
                # criterion in r,g,b coordinates.
                # Although costly, this would be a CPU burden only when
                # sorting columns with color information. For now, only
                # the Plotted Lines line list has such information, and
                # the number of actually plotted lines tends to be small
                # anyway.
                if isinstance(cell, QColor):
                    r = cell.red()
                    g = cell.green()
                    b = cell.blue()
                    min_dist = 100000
                    result = cell
                    for color_name, orig_color in ID_COLORS.items():
                        orig_rgb = QColor(orig_color)
                        dist = abs(orig_rgb.red() - r) + abs(orig_rgb.green() - g) + abs(orig_rgb.blue() - b)
                        if dist < min_dist:
                            min_dist = dist
                            result = orig_color

                    key = [k for k,value in ID_COLORS.items() if value == result][0]

                    cells.append(QVariant(key))

                else:
                    cells.append(QVariant(str(cell)))

            self._row_cells.append(cells)

            self._nrows = len(self._row_cells)
            self._ncols = len(self._row_cells[0])

    def rowCount(self, parent=None, *args, **kwargs):
        """
        Overrides the base class
        """
        # this has to use a pre-computed number of rows,
        # otherwise sorting gets significantly slowed
        # down. Same for number of columns.
        return self._nrows

    def columnCount(self, parent=None, *args, **kwargs):
        """
        Overrides the base class
        """
        return self._ncols

    def data(self, index, role=None):
        """
        Overrides the base class
        """
        if role != Qt.DisplayRole:
            return QVariant()

        # This is the main bottleneck for sorting. Profiling experiments
        # show that the main culprit is the .columns[][] accessor in the
        # astropy table. The index.column() and index.row() calls cause
        # negligible CPU load.
        #
        # return self._linelist.columns[index.column()][index.row()]
        #
        # going from an astropy table to a list of rows, the bottleneck
        # narrows down to the astropy code that gets a cell value from a
        # Row instance.
        return self._row_cells[index.row()][index.column()]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Overrides the base class
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._linelist.colnames[section]

        # This generates tooltips for header cells
        if role == Qt.ToolTipRole and orientation == Qt.Horizontal:
            if self._linelist.colnames[section] in [WAVELENGTH_COLUMN, ERROR_COLUMN]:
                result = self._linelist.columns[section].unit
            else:
                # this captures glitches that generate None tooltips
                if self._linelist.tooltips:
                    result = self._linelist.tooltips[section]
                else:
                    result = ''
            return str(result)

        return QAbstractTableModel.headerData(self, section, orientation, role)

    def get_name(self):
        """
        Gets the name of the line list

        Returns
        -------
        the name of the line list
        """
        return self._linelist.name


class SortModel(QSortFilterProxyModel):
    """
    A sorting model for line list columns.

    Parameters
    ----------
    name : str
        The line list name.

    """

    def __init__(self, name):
        super(SortModel, self).__init__()

        self._name = name

    def lessThan(self, left, right):
        """
        Overrides the base class
        """
        left_data = left.data()
        right_data = right.data()

        # it's enough to find type using just one of the parameters,
        # since they both necessarily come from the same table column.
        try:
            l = float(left_data)
            r = float(right_data)
            return l < r
        except:
            # Lexicographic string comparison. The parameters passed
            # to this method from a sortable table model are stored
            # in QtCore.QModelIndex instances.
            return str(left_data) < str(right_data)

    def get_name(self):
        """
        Gets the name of the line list

        Returns
        -------
        the name of the line list
        """
        return self._name
