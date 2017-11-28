"""
Define all the line list-based windows and dialogs
"""
import os

from qtpy.QtWidgets import (QWidget, QGridLayout, QHBoxLayout, QLabel,
                            QPushButton, QTabWidget, QVBoxLayout, QSpacerItem,
                            QMenu, QMenuBar, QSizePolicy, QToolBar, QStatusBar,
                            QAction, QTableView, QMainWindow,
                            QAbstractItemView, QLayout, QTextBrowser, QComboBox)
from qtpy.QtGui import QPixmap, QIcon, QColor, QStandardItem, QLineEdit, QDoubleValidator, QHeaderView
from qtpy.QtCore import (QSize, QRect, QCoreApplication, QMetaObject, Qt,
                         QAbstractTableModel, QVariant, QSortFilterProxyModel)

from ..core.events import dispatch

from ..core.linelist import WAVELENGTH_COLUMN, ERROR_COLUMN, DEFAULT_HEIGHT

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


#TODO work in progress

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
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setGeometry(QRect(0, 0, 767, 22))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QToolBar(MainWindow)
        self.mainToolBar.setMovable(False)
        self.mainToolBar.setFloatable(False)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.actionOpen = QAction(MainWindow)
        icon = QIcon(os.path.join(ICON_PATH, "Open Folder-48.png"))
        self.actionOpen.setIcon(icon)
        self.actionOpen.setObjectName("actionOpen")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionRemove = QAction(MainWindow)
        self.actionRemove.setObjectName("actionRemove")
        self.actionChange_Color = QAction(MainWindow)
        self.actionChange_Color.setObjectName("actionChange_Color")
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.mainToolBar.addAction(self.actionOpen)
        self.mainToolBar.addSeparator()

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
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        # self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionRemove.setText(_translate("MainWindow", "Remove"))
        self.actionRemove.setToolTip(_translate("MainWindow", "Removes the selected layer"))
        self.actionChange_Color.setText(_translate("MainWindow", "Change Color"))
        self.actionChange_Color.setToolTip(_translate("MainWindow", "Change the line color selected layer"))


class ClosableMainWindow(QMainWindow):
    # this exists just to ensure that a window closing event
    # that is generated by the OS itself, gets properly handled.
    def closeEvent(self, event):
        dispatch.on_dismiss_linelists_window.emit()


class LineListsWindow(UiLinelistsWindow):
    def __init__(self, plot_window, parent=None):
        super(LineListsWindow, self).__init__()

        # Builds GUI
        self._main_window = ClosableMainWindow()
        self.setupUi(self._main_window, str(plot_window))

        # Request that line lists be read from wherever are they sources.
        dispatch.on_request_linelists.emit()

        self._buildViews(plot_window)

        # # Add tool tray buttons
        # self.button_open_data = self.add_tool_bar_actions(
        #     name="Open",
        #     description='Open data file',
        #     icon_path=os.path.join(ICON_PATH, "Open Folder-48.png"),
        #     category=('Loaders', 5),
        #     priority=1,
        #     callback=lambda: dispatch.on_file_open.emit())





        # Connect buttons to appropriate signals.
        #
        # Note that, for the Draw operation, we have to pass the table views to
        # the handler, even though it would be better to handle the row selections
        # all in here for the sake of encapsulation. This is so because this class
        # is not a QWidget or one of its subclasses, thus it cannot implement a
        # DispatchHandle signal handler.
        self.draw_button.clicked.connect(lambda:dispatch.on_plot_linelists.emit(
            table_views=self._table_views,
            tabbed_panes=self._tabbed_panes,
            units=plot_window.waverange[0].unit))
        self.erase_button.clicked.connect(dispatch.on_erase_linelabels.emit)
        self.dismiss_button.clicked.connect(dispatch.on_dismiss_linelists_window.emit)

    def _buildViews(self, plot_window):

        # Table views must be preserved in the instance so they can be
        # passed to whoever is going to do the actual line list plotting.
        # The plotting code must know which lines (table rows) are selected
        # in each line list.
        self._table_views = []
        self._tabbed_panes = []
        self._plotted_lines_pane = QWidget()

        for linelist in plot_window.linelists:

            table_model = LineListTableModel(linelist)

            if table_model.rowCount() > 0:
                table_view = QTableView()

                # disabling sorting will significantly speed up the
                # rendering, in particular of large line lists. These lists are
                # often jumbled in wavelength, and consequently difficult
                # to read and use, so having a sorting option is useful indeed.
                # It remains to be seen what would be the approach users will
                # favor. We might add a toggle that users can set/reset depending
                # on their preferences.
                table_view.setSortingEnabled(False)
                proxy = SortModel(table_model.getName())
                proxy.setSourceModel(table_model)
                table_view.setModel(proxy)
                table_view.setSortingEnabled(True)
                table_view.horizontalHeader().setStretchLastSection(True)

                # playing with these doesn't speed up the sorting,
                # regardless of whatever you may read on the net.
                # table_view.horizontalHeader().setResizeMode(QHeaderView.Fixed)
                # table_view.verticalHeader().setResizeMode(QHeaderView.Fixed)
                # table_view.horizontalHeader().setStretchLastSection(False)
                # table_view.verticalHeader().setStretchLastSection(False)

                table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
                table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
                table_view.resizeColumnsToContents()
                comments = linelist.meta['comments']

                # this preserves the original sorting state
                # of the list. Use zero to sort by wavelength
                # on load. Doesn't seem to affect performance
                # by much tough.
                proxy.sort(-1, Qt.AscendingOrder)

                # table selections will change the total count of lines selected.
                selectionModel = table_view.selectionModel()
                selectionModel.selectionChanged.connect(self._countSelections)

                pane = LineListPane(table_view, comments)

                self.tabWidget.addTab(pane, table_model.getName())

                self._table_views.append(table_view)
                self._tabbed_panes.append(pane)

        self._index_plotted = self.tabWidget.addTab(QWidget(), PLOTTED)

    def displayPlottedLines(self, linelist):
        self._plotted_lines_pane = PlottedLinesPane(linelist)
        self.tabWidget.removeTab(self._index_plotted)
        self._index_plotted = self.tabWidget.insertTab(self._index_plotted, self._plotted_lines_pane, PLOTTED)

    def erasePlottedLines(self):
        self.tabWidget.removeTab(self._index_plotted)
        self._index_plotted = self.tabWidget.addTab(QWidget(), PLOTTED)

    def _countSelections(self):
        count = 0
        for table_view in self._table_views:
            count += len(table_view.selectionModel().selectedRows())
        self.lines_selected_label.setText(str(count))

        color = 'black' if count < 500 else 'red'
        self.lines_selected_label.setStyleSheet('color:'+color)

    def show(self):
        self._main_window.show()

    def hide(self):
        self._main_window.hide()


class LineListPane(QWidget):

    # this builds a single pane dedicated to a single list.

    def __init__(self, table_view, comments, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

        layout = QVBoxLayout()
        layout.setSizeConstraint(QLayout.SetMaximumSize)
        self.setLayout(layout)

        # header with line list metadata.
        info = QTextBrowser()
        info.setMaximumHeight(100)
        info.setAutoFillBackground(True)
        info.setStyleSheet("background-color: rgb(230,230,230);")

        for comment in comments:
            info.append(comment)

        # buttons and selectors dedicated to the specific list
        # displayed in this pane.
        button_pane = QWidget()
        # hlayout = QHBoxLayout()
        hlayout = QGridLayout()

        # 'add set' button
        self.create_set_button = QPushButton(self)
        self.create_set_button.setObjectName("add_set_button")
        _translate = QCoreApplication.translate
        self.create_set_button.setText(_translate("MainWindow", "Create set"))
        self.create_set_button.setToolTip("Create new line set from selected lines.")
        self.create_set_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        hlayout.addWidget(self.create_set_button, 1, 0)
        self.create_set_button.setEnabled(False)

        # 'deselect all' button
        deselect_button = QPushButton(self)
        deselect_button.setObjectName("deselect_button")
        _translate = QCoreApplication.translate
        deselect_button.setText(_translate("MainWindow", "Deselect"))
        deselect_button.setToolTip("Un-select everything on this set.")
        deselect_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        hlayout.addWidget(deselect_button,1, 1)
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
        for uname in ['z','km/s']:
            item = QStandardItem(uname)
            model.appendRow(item)
        hlayout.addWidget(self.combo_box_z_units, 1, 5)

        # put it all together.
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        hlayout.addItem(spacerItem, 1, 6)
        button_pane.setLayout(hlayout)

        layout.addWidget(info)
        layout.addWidget(table_view)
        layout.addWidget(button_pane)


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
            proxy = SortModel(table_model.getName(), )
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
                result = self._linelist.tooltips[section]
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
        if type(left_data) == float:
            return float(left_data) < float(right_data)
        else:
            # Lexicographic string comparison. The parameters passed
            # to this method from a sortable table model are stored
            # in QtCore.QModelIndex instances.
            return str(left_data) < str(right_data)

    def getName(self):
        return self._name
