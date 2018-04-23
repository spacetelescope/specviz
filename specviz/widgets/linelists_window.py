"""
Define all the line list-based windows and dialogs
"""
import os

from qtpy.QtWidgets import (QWidget, QGridLayout, QHBoxLayout, QLabel,
                            QPushButton, QTabWidget, QVBoxLayout, QSpacerItem,
                            QSizePolicy, QToolBar, QLineEdit, QTabBar,
                            QAction, QTableView, QMainWindow, QHeaderView,
                            QAbstractItemView, QLayout, QTextBrowser, QComboBox,
                            QDialog, QErrorMessage)
from qtpy.QtGui import QIcon, QColor, QStandardItem, \
                       QDoubleValidator, QFont
from qtpy.QtCore import (QSize, QCoreApplication, QMetaObject, Qt,
                         QAbstractTableModel, QVariant, QSortFilterProxyModel)
from qtpy import compat

from astropy.units import Quantity
from astropy.units.core import UnitConversionError
from astropy.io import ascii

from ..core.events import dispatch
from ..core import linelist
from ..core.linelist import WAVELENGTH_COLUMN, ERROR_COLUMN, DEFAULT_HEIGHT
from ..core.linelist import columns_to_remove

ICON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', 'data', 'qt', 'resources'))

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

wave_range = (None, None)


# Function that creates one single tabbed pane with one single view of a line list.

def _createLineListPane(linelist, table_model, caller):

    table_view = QTableView()

    # disabling sorting will significantly speed up the rendering,
    # in particular of large line lists. These lists are often jumbled
    # in wavelength, and consequently difficult to read and use, so
    # having a sorting option is useful indeed. It remains to be seen
    # what would be the approach users will favor. We might add a toggle
    # that users can set/reset depending on their preferences.
    table_view.setSortingEnabled(False)
    sort_proxy = SortModel(table_model.getName())
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


# The line list window must be a full fledged window and not a dialog.
# Dialogs do not support things like menu bars and central widgets.
# They are also a bit cumbersome to use when modal behavior is of no
# importance. Lets try to treat this as a window for now, and see how
# it goes.

class UiLinelistsWindow(object):

    # this code was taken as-is from the Designer.
    # Cleaning it up sounds like a lower priority
    # task for now.
    def setupUi(self, MainWindow, title):
        MainWindow.setWindowTitle(title)
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 850)
        MainWindow.setMinimumSize(QSize(300, 350))
        self.centralWidget = QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.gridLayout = QGridLayout(self.centralWidget)
        self.gridLayout.setContentsMargins(11, 11, 11, 11)
        self.gridLayout.setSpacing(6)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.lines_selected_label = QLabel(self.centralWidget)
        self.lines_selected_label.setObjectName("lines_selected_label")
        self.horizontalLayout_5.addWidget(self.lines_selected_label)
        self.label = QLabel(self.centralWidget)
        self.label.setObjectName("label")
        self.horizontalLayout_5.addWidget(self.label)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.draw_button = QPushButton(self.centralWidget)
        self.draw_button.setObjectName("draw_button")
        self.horizontalLayout_5.addWidget(self.draw_button)
        self.erase_button = QPushButton(self.centralWidget)
        self.erase_button.setObjectName("erase_button")
        self.horizontalLayout_5.addWidget(self.erase_button)
        self.dismiss_button = QPushButton(self.centralWidget)
        self.dismiss_button.setObjectName("dismiss_button")
        self.horizontalLayout_5.addWidget(self.dismiss_button)
        self.gridLayout.addLayout(self.horizontalLayout_5, 4, 0, 1, 1)
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout_11.setSpacing(6)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.tabWidget = QTabWidget(self.centralWidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tabWidget.setTabsClosable(True)
        self.verticalLayout_11.addWidget(self.tabWidget)
        self.gridLayout.addLayout(self.verticalLayout_11, 0, 0, 1, 1)
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_7.setSpacing(6)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_7.addItem(spacerItem)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.gridLayout.addLayout(self.horizontalLayout_7, 2, 0, 2, 1)
        MainWindow.setCentralWidget(self.centralWidget)

        # self.menuBar = QMenuBar(MainWindow)
        # self.menuBar.setGeometry(QRect(0, 0, 767, 22))
        # self.menuBar.setObjectName("menuBar")
        #
        # self.menuFile = QMenu(self.menuBar)
        # self.menuFile.setObjectName("menuFile")
        #
        # MainWindow.setMenuBar(self.menuBar)

        self.mainToolBar = QToolBar(MainWindow)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setFloatable(False)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.mainToolBar)

        # self.statusBar = QStatusBar(MainWindow)
        # self.statusBar.setObjectName("statusBar")
        # MainWindow.setStatusBar(self.statusBar)

        self.actionOpen = QAction(MainWindow)
        icon = QIcon(os.path.join(ICON_PATH, "Open Folder-48.png"))
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")

        self.actionExport = QAction(MainWindow)
        icon = QIcon(os.path.join(ICON_PATH, "Export-48.png"))
        self.actionExport.setIcon(icon)
        self.actionExport.setObjectName("actionExport")

        self.line_list_selector = QComboBox()
        self.line_list_selector.setToolTip("Select line list from internal library")

        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionRemove = QAction(MainWindow)
        self.actionRemove.setObjectName("actionRemove")
        self.actionChange_Color = QAction(MainWindow)
        self.actionChange_Color.setObjectName("actionChange_Color")
        # self.menuFile.addAction(self.actionOpen)
        # self.menuFile.addSeparator()
        # self.menuFile.addAction(self.actionExit)
        # self.menuBar.addAction(self.menuFile.menuAction())
        self.mainToolBar.addAction(self.actionOpen)
        self.mainToolBar.addAction(self.actionExport)
        self.mainToolBar.addSeparator()
        self.mainToolBar.addWidget(self.line_list_selector)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        self.lines_selected_label.setText(_translate("MainWindow", "0"))
        self.lines_selected_label.setToolTip("Total number of lines selected in all sets.")
        self.label.setText(_translate("MainWindow", "lines selected"))
        self.label.setToolTip("Total number of lines selected in all sets.")
        self.draw_button.setText(_translate("MainWindow", "Draw"))
        self.draw_button.setToolTip("Plot markers for all selected lines in all sets.")
        self.erase_button.setText(_translate("MainWindow", "Erase"))
        self.erase_button.setToolTip("Erase all markers")
        self.dismiss_button.setText(_translate("MainWindow", "Dismiss"))
        self.dismiss_button.setToolTip("Dismiss this window")
        # self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionExport.setText(_translate("MainWindow", "Export plotted lines"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionRemove.setText(_translate("MainWindow", "Remove"))
        self.actionRemove.setToolTip(_translate("MainWindow", "Removes the selected layer"))
        self.actionChange_Color.setText(_translate("MainWindow", "Change Color"))
        self.actionChange_Color.setToolTip(_translate("MainWindow", "Change the line color selected layer"))


class ClosableMainWindow(QMainWindow):
    # this exists just to ensure that a window closing event
    # that is generated by the OS itself, gets properly handled.
    def closeEvent(self, event):
        dispatch.on_dismiss_linelists_window.emit(close=False)


class LineListsWindow(UiLinelistsWindow):

    def __init__(self, plot_window, parent=None):
        super(LineListsWindow, self).__init__()

        self.plot_window = plot_window

        # Builds GUI
        self._main_window = ClosableMainWindow()
        self.setupUi(self._main_window, str(plot_window))
        self.tabWidget.tabCloseRequested.connect(self.tab_close)

        # Request that line lists be read from wherever are they sources.
        dispatch.on_request_linelists.emit()

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

        #------------ UNCOMMENT TO LOAD LISTS AUTOMATICALLY --------------
        #
        # Populate GUI.
        #
        # This is commented out for now to comply with the decision about
        # not showing any line list automatically upon startup. In case
        # we need that capability back, just uncomment this line.

        # self._buildViews(plot_window)

        #---------------------------------------------------------------

        # Connect controls to appropriate signals.
        #
        # Note that, for the Draw operation, we have to pass the table views to
        # the handler, even though it would be better to handle the row selections
        # all in here for the sake of encapsulation. This is so because this class
        # is not a QWidget or one of its subclasses, thus it cannot implement a
        # DispatchHandle signal handler.
        self.draw_button.clicked.connect(lambda:dispatch.on_plot_linelists.emit(
            table_views=self._getTableViews(),
            panes=self._getPanes(),
            units=plot_window.waverange[0].unit,
            caller=plot_window))

        self.erase_button.clicked.connect(lambda:dispatch.on_erase_linelabels.emit(caller=plot_window))
        self.dismiss_button.clicked.connect(lambda:dispatch.on_dismiss_linelists_window.emit(close=False))
        self.actionOpen.triggered.connect(lambda:self._open_linelist_file(file_name=None))
        self.actionExport.triggered.connect(lambda:self._export_to_file(file_name=None))
        self.line_list_selector.currentIndexChanged.connect(self._lineList_selection_change)

    def _get_waverange_from_dialog(self, line_list):
        # there is a widget-wide wavelength range so as to preserve
        # the user definition from call to call. At the initial
        # call, the wave range is initialized with whatever range
        # is being displayed in the spectrum plot window.
        global wave_range
        if wave_range[0] == None or wave_range[1] == None:
            wave_range = self.plot_window._find_wavelength_range()

        wrange = self._build_waverange_dialog(wave_range, line_list)

        wave_range = wrange

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
                    global wave_range
                    if wave_range[0] and wave_range[1]:
                        line_list = self._build_view(line_list, 0, waverange=wave_range)
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

    def _lineList_selection_change(self, index):
        # ignore first element in drop down. It contains
        # the "Select line list" message.
        if index > 0:
            line_list = linelist.get_from_cache(index-1)

            try:
                self._get_waverange_from_dialog(line_list)
                global wave_range
                if wave_range[0] and wave_range[1]:
                    self._build_view(line_list, 0, waverange=wave_range)

                self.line_list_selector.setCurrentIndex(0)

            except UnitConversionError as err:
                error_dialog = QErrorMessage()
                error_dialog.showMessage('Units conversion not possible.')
                error_dialog.exec_()

    def _build_waverange_dialog(self, wave_range, line_list):

        dialog = QDialog(parent=self.centralWidget)
        dialog.setWindowTitle("Wavelength range")
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.resize(370, 250)

        button_ok = QPushButton("OK")
        button_ok.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button_cancel = QPushButton("Cancel")
        button_cancel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        button_ok.clicked.connect(dialog.accept)
        button_cancel.clicked.connect(dialog.reject)

        min_text = QLineEdit("%.2f" % wave_range[0].value)
        max_text = QLineEdit("%.2f" % wave_range[1].value)

        validator = QDoubleValidator()
        validator.setBottom(0.0)
        validator.setDecimals(2)
        min_text.setValidator(validator)
        max_text.setValidator(validator)

        min_text.setFixedWidth(150)
        max_text.setFixedWidth(150)
        min_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        max_text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        min_text.setToolTip("Minimum wavelength to read from list.")
        max_text.setToolTip("Maximum wavelength to read from list.")

        nlines_label = self._compute_nlines_in_waverange(line_list, min_text, max_text)

        min_text.editingFinished.connect(lambda: self._compute_nlines_in_waverange(line_list,
                                                 min_text, max_text, label=nlines_label))
        max_text.editingFinished.connect(lambda: self._compute_nlines_in_waverange(line_list,
                                                 min_text, max_text, label=nlines_label))

        # set up layouts and widgets for the dialog.
        text_pane = QWidget()
        text_layout = QGridLayout()

        text_layout.addWidget(min_text, 1, 0)
        text_layout.addWidget(QLabel("Minimum wavelength"), 0, 0)
        text_layout.addWidget(max_text, 1, 1)
        text_layout.addWidget(QLabel("Maximum wavelength"), 0, 1)

        spacerItem = QSpacerItem(40, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)
        text_layout.addItem(spacerItem, 1, 2)
        text_pane.setLayout(text_layout)

        label_pane = QWidget()
        label_layout = QHBoxLayout()
        label_layout.addWidget(nlines_label)
        label_layout.addWidget(QLabel(" lines included in range."))
        label_layout.addStretch()
        label_pane.setLayout(label_layout)

        button_pane = QWidget()
        button_layout = QHBoxLayout()

        button_layout.addStretch()
        button_layout.addWidget(button_cancel)
        button_layout.addWidget(button_ok)
        button_pane.setLayout(button_layout)

        dialog_layout = QVBoxLayout()
        dialog_layout.setSizeConstraint(QLayout.SetMaximumSize)

        dialog_layout.addWidget(text_pane)
        dialog_layout.addWidget(label_pane)
        dialog_layout.addStretch()
        dialog_layout.addWidget(button_pane)

        dialog.setLayout(dialog_layout)

        button_ok.setDefault(True)
        button_cancel.setDefault(False)

        accepted = dialog.exec_() > 0

        amin = amax = None
        if accepted:
            return self._get_range_from_textfields(min_text, max_text)

        return (amin, amax)

    def _get_range_from_textfields(self, min_text, max_text):
        amin = amax = None
        if min_text.hasAcceptableInput() and max_text.hasAcceptableInput():
            amin = float(min_text.text())
            amax = float(max_text.text())
            if amax > amin:
                units = self.plot_window._plot_units[0]
                amin = Quantity(amin, units)
                amax = Quantity(amax, units)
            else:
                return (None, None)

        return (amin, amax)

    # computes how many lines in the supplied list
    # fall within the supplied wavelength range. The
    # result populates the supplied label. Or, it
    # builds a fresh QLabel with the result.
    def _compute_nlines_in_waverange(self, line_list, min_text, max_text, label=None):

        amin, amax = self._get_range_from_textfields(min_text, max_text)

        if amin != None or amax != None:
            r = (amin, amax)
            extracted = line_list.extract_range(r)
            nlines = len(extracted[WAVELENGTH_COLUMN].data)

            if label == None:
                label = QLabel(str(nlines))
            else:
                label.setText(str(nlines))
            color = 'black' if nlines < NLINES_WARN else 'red'
            label.setStyleSheet('color:' + color)

        return label

    def _build_view(self, line_list, index, waverange=(None,None)):

        if waverange[0] and wave_range[1]:
            line_list = line_list.extract_range(waverange)

        table_model = LineListTableModel(line_list)

        if table_model.rowCount() > 0:
            # here we add the first pane (the one with the entire
            # original line list), to the tabbed pane that contains
            # the line sets corresponding to the current line list.
            lineset_tabbed_pane = QTabWidget()
            lineset_tabbed_pane.setTabsClosable(True)

            pane, table_view = _createLineListPane(line_list, table_model, self)
            lineset_tabbed_pane.addTab(pane, "Original")
            pane.setLineSetsTabbedPane(lineset_tabbed_pane)

            # connect signals
            table_view.selectionModel().selectionChanged.connect(self._countSelections)
            table_view.selectionModel().selectionChanged.connect(pane.handle_button_activation)

            # now we add this "line set tabbed pane" to the main tabbed
            # pane, with name taken from the list model.
            self.tabWidget.insertTab(index, lineset_tabbed_pane, table_model.getName())
            self.tabWidget.setCurrentIndex(index)

            # store for use down stream.
            # self.table_views.append(table_view)
            # self.set_tabbed_panes.append(set_tabbed_pane)
            # self.tab_count.append(0)
            # self.panes.append(pane)

            return line_list

    def _buildViews(self, plot_window):
        window_linelists = plot_window.linelists
        for linelist, index  in zip(window_linelists, range(len(window_linelists))):
            self._build_view(linelist, index)

        # add extra tab to hold the plotted lines view.
        widget_count = self.tabWidget.count()
        if widget_count > 0:
            self.tabWidget.addTab(QWidget(), PLOTTED)
            self.tabWidget.tabBar().setTabButton(widget_count-1, QTabBar.LeftSide, None)

    def tab_close(self, index):
        self.tabWidget.removeTab(index)

    def displayPlottedLines(self, linelist):
        self._plotted_lines_pane = PlottedLinesPane(linelist)

        for index in range(self.tabWidget.count()):
            tab_text = self.tabWidget.tabText(index)
            if tab_text == PLOTTED:
                self.tabWidget.removeTab(index)
                self.tabWidget.insertTab(index, self._plotted_lines_pane, PLOTTED)
                return

        # if no plotted pane yet, create one.
        index = self.tabWidget.count()
        self.tabWidget.insertTab(index, self._plotted_lines_pane, PLOTTED)

    def erasePlottedLines(self):
        index_last = self.tabWidget.count() - 1
        self.tabWidget.removeTab(index_last)
        self.tabWidget.addTab(QWidget(), PLOTTED)

    # computes total of rows selected in all table views in all panes
    # and displays result in GUI.
    def _countSelections(self):
        panes = self._getPanes()
        sizes = [len(pane.table_view.selectionModel().selectedRows()) for pane in panes]
        import functools
        count = functools.reduce(lambda x,y: x+y, sizes)

        # display total selected rows, with eventual warning.
        self.lines_selected_label.setText(str(count))
        color = 'black' if count < NLINES_WARN else 'red'
        self.lines_selected_label.setStyleSheet('color:'+color)

    # these two methods below return a flat rendering of the panes
    # and table views stored in the two-tiered tabbed window. These
    # flat renderings are required by the drawing code.

    def _getTableViews(self):
        panes = self._getPanes()
        return [pane.table_view for pane in panes]

    def _getPanes(self):
        result = []
        for index_1 in range(self.tabWidget.count()):
            widget = self.tabWidget.widget(index_1)
            if isinstance(widget, QTabWidget) and self.tabWidget.tabText(index_1) != PLOTTED:
                # do not use list comprehension here!
                for index_2 in range(widget.count()):
                    result.append(widget.widget(index_2))
        return result

    def show(self):
        self._main_window.show()

    def hide(self):
        self._main_window.hide()

    def close(self):
        self._main_window.close()


class LineListPane(QWidget):

    # this builds a single pane dedicated to a single list.

    def __init__(self, table_view, linelist, sort_proxy, caller, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

        self.table_view = table_view
        self.linelist = linelist
        self._sort_proxy = sort_proxy
        self._caller = caller

        self._build_GUI(linelist, table_view)

    def _build_GUI(self, linelist, table_view):
        panel_layout = QVBoxLayout()
        panel_layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.setLayout(panel_layout)
        # header with line list metadata.
        info = QTextBrowser()
        info.setMaximumHeight(100)
        info.setAutoFillBackground(True)
        info.setStyleSheet("background-color: rgb(230,230,230);")
        for comment in linelist.meta['comments']:
            info.append(comment)

        # buttons and selectors dedicated to the specific list
        # displayed in this pane.
        button_pane = QWidget()
        hlayout = QGridLayout()

        # 'add set' button
        self.create_set_button = QPushButton(self)
        self.create_set_button.setObjectName("add_set_button")
        _translate = QCoreApplication.translate
        self.create_set_button.setText(_translate("MainWindow", "Create set"))
        self.create_set_button.setToolTip("Create new line set from selected lines.")
        self.create_set_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        hlayout.addWidget(self.create_set_button, 1, 0)

        # the create_set button is enabled/disabled by logic elsewhere
        self.create_set_button.setEnabled(False)
        self.create_set_button.clicked.connect(lambda: self._createSet())

        # 'deselect all' button
        deselect_button = QPushButton(self)
        deselect_button.setObjectName("deselect_button")
        _translate = QCoreApplication.translate
        deselect_button.setText(_translate("MainWindow", "Deselect"))
        deselect_button.setToolTip("Un-select everything on this set.")
        deselect_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        hlayout.addWidget(deselect_button, 1, 1)
        deselect_button.clicked.connect(lambda: table_view.clearSelection())

        # color picker
        self.combo_box_color = QComboBox(self)
        self.combo_box_color.setObjectName("color_selector")
        self.combo_box_color.setToolTip("Color for selected lines in this set.")
        model = self.combo_box_color.model()
        for cname in ID_COLORS:
            item = QStandardItem(cname)
            item.setForeground(ID_COLORS[cname])
            item.setData(QColor(ID_COLORS[cname]), role=Qt.UserRole)
            model.appendRow(item)
        hlayout.addWidget(self.combo_box_color, 1, 2)
        hlayout.addWidget(QLabel("Color"), 0, 2)

        # plotting height
        self.height_textbox = QLineEdit(str(DEFAULT_HEIGHT))
        validator = QDoubleValidator()
        validator.setRange(0.05, 0.95, decimals=2)
        self.height_textbox.setValidator(validator)
        self.height_textbox.setFixedWidth(50)
        self.height_textbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.height_textbox.setToolTip("Relative height to plot.")
        hlayout.addWidget(self.height_textbox, 1, 3)
        hlayout.addWidget(QLabel("Height"), 0, 3)

        # redshift
        self.redshift_textbox = QLineEdit(str(0.0))
        validator = QDoubleValidator()
        validator.setRange(-1.e5, 1.e10, decimals=4)
        self.redshift_textbox.setValidator(validator)
        self.redshift_textbox.setFixedWidth(70)
        self.redshift_textbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.redshift_textbox.setToolTip("Redshift lines by")
        hlayout.addWidget(self.redshift_textbox, 1, 4)
        hlayout.addWidget(QLabel("Redshift"), 0, 4)

        # redshift units
        self.combo_box_z_units = QComboBox(self)
        self.combo_box_z_units.setObjectName("redshift_units")
        self.combo_box_z_units.setToolTip("Redshift units.")
        model = self.combo_box_z_units.model()
        for uname in ['z', 'km/s']:
            item = QStandardItem(uname)
            model.appendRow(item)
        hlayout.addWidget(self.combo_box_z_units, 1, 5)

        # put it all together.
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout.addItem(spacerItem, 1, 6)
        button_pane.setLayout(hlayout)

        panel_layout.addWidget(info)
        panel_layout.addWidget(table_view)
        panel_layout.addWidget(button_pane)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def setLineSetsTabbedPane(self, pane):
        self._sets_tabbed_pane = pane

        # this must be set only once per tabbed pane, otherwise multiple
        # signal handlers can result in more than one tab being closed
        # when just one closing request is posted.
        self._sets_tabbed_pane.tabCloseRequested.connect(self.tab_close)

    def _createSet(self):
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
            pane, table_view = _createLineListPane(local_list, table_model, self._caller)

            pane._sets_tabbed_pane = self._sets_tabbed_pane
            table_view.selectionModel().selectionChanged.connect(self._caller._countSelections)
            table_view.selectionModel().selectionChanged.connect(pane.handle_button_activation)

            self._sets_tabbed_pane.addTab(pane, str(self._sets_tabbed_pane.count()))

    def tab_close(self, index):
        self._sets_tabbed_pane.removeTab(index)

    def handle_button_activation(self):
        nselected = len(self.table_view.selectionModel().selectedRows())
        self.create_set_button.setEnabled(nselected > 0)


class PlottedLinesPane(QWidget):

    # This holds the list with the currently plotted lines.
    #
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
    # might suffice, perhaps).

    def __init__(self, plotted_lines, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

        self.plotted_lines = plotted_lines

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.setLayout(layout)

        table_model = LineListTableModel(plotted_lines)
        if table_model.rowCount() > 0:
            table_view = QTableView()

            # disabling sorting will significantly speed up the
            # plot. This is because the table view must be re-built
            # every time a new set of markers is drawn on the plot
            # surface. Alternate approaches are worth examining. It
            # remains to be seen what would be the approach users
            # will favor.

            table_view.setSortingEnabled(False)
            proxy = SortModel(table_model.getName())
            proxy.setSourceModel(table_model)
            table_view.setModel(proxy)
            table_view.setSortingEnabled(True)

            table_view.setSelectionMode(QAbstractItemView.NoSelection)
            table_view.horizontalHeader().setStretchLastSection(True)
            table_view.resizeColumnsToContents()

            layout.addWidget(table_view)


class LineListTableModel(QAbstractTableModel):

    def __init__(self, linelist, parent=None, *args):

        QAbstractTableModel.__init__(self, parent, *args)

        self._linelist = linelist

        #TODO move entire table contents to an array of QVector
        # instances that will store the columns. This should
        # speed up the sorting (as far as some indications in
        # the net suggest:
        # http://www.qtforum.org/article/30638/qsortfilterproxymodel-qtreeview-sort-performance.html).
        # Bummer... this is C++ only; PyQt never went to the trouble
        # of converting QVector it to python.
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
        # this has to use a pre-computed number of rows,
        # otherwise sorting gets significantly slowed
        # down. Same for number of columns.
        return self._nrows

    def columnCount(self, parent=None, *args, **kwargs):
        return self._ncols

    def data(self, index, role=None):
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

    def getName(self):
        return self._linelist.name


class SortModel(QSortFilterProxyModel):

    def __init__(self, name):
        super(SortModel, self).__init__()

        self._name = name

    def lessThan(self, left, right):
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

    def getName(self):
        return self._name


