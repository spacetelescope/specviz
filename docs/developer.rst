Developer Documentation
=======================

This set of documentation focuses on the structure of SpecViz, its various
pieces, and how they work together.

Data Model
----------

The central piece of SpecViz is the internal Qt data model expressed in the
:class:`~specviz.core.models.DataListModel` class. It is responsible
for maintaining the collection of :class:`~specutils.Spectrum1D` objects and
exposing them as Qt :class:`specviz.core.items.DataItem`s.

In the context of SpecViz, the :class:`~specutils.Spectrum1D` is considered
immutable. In a similar sense, :class:`specviz.core.items.DataItem` is only a
Qt interface to an *instance* of the :class:`~specutils.Spectrum1D` class. As
such, it is possible to change which :class:`~specutils.Spectrum1D` the
:class:`specviz.core.items.DataItem` contains, but otherwise exposes no other
means to mutate the item.

While SpecViz contains Qt view widgets that expose
:class:`~specviz.core.models.DataListModel`s (e.g. `QListView`), this is
generally not done directly. Instead, a proxy model (:class:`~specviz.core.models.PlotProxyModel`)
is used to wrap and expose the :class:`~specviz.core.items.DataItem` items as
:class:`~specviz.core.items.PlotDataItem`s. These are fundamentally
different from the :class:`specviz.core.items.DataItem`s in that they contain
mutable attributes that determine how the :class:`specviz.core.items.DataItem`
they contain will be expressed in SpecViz. This ranges from whether or not the
item is hidden, what its current plot color is, what its currently user-defined
name is, etc. They are also workspace-specific, and not application-specific
like the :class:`~specviz.core.models.PlotProxyModel` and
:class:`~specviz.core.items.PlotDataItem`s.

Application and Workspaces
--------------------------

The :class:`~specviz.app.Application` is the singular Qt application instance
run to begin interacting with SpecViz. It is within this class that
:class:`~specviz.widgets.workspace.Workspace` instances are generated and
maintained. It contains methods for adding, removing, and retrieving
workspaces to the application instance. This class is also responsible for
parsing and loading any plugins that exist in the `plugins` directory as well
as adding them to the plugin registry maintained by an instance of the
:class:`~specviz.core.plugin.Plugin` class (more on this in the <Plugins>
section).

Within a single SpecViz application, multiple, independent
:class:`~specviz.widgets.workspace.Workspace`s can be created. Each workspace
its own internal :class:`~specviz.core.models.DataListModel` and therefore
maintains a completely separate set of data items. Workspaces themselves
contain all the interactive elements a user will see, including the main
tool bar, the data items list, plugins, and any number of
:class:`~specviz.widgets.plotting.PlotWindow` instances. The display of the
data items is handled by the :class:`~specviz.core.models.PlotProxyModel`,
and this list of :class:`~specviz.core.models.PlotProxyModel` is particular to
a single :class:`~specviz.widgets.plotting.PlotWindow`. Opening multiple
:class:`~specviz.widgets.plotting.PlotWindow`s will result in as many
:class:`~specviz.core.models.PlotProxyModel`s. This is helpful for performance
reasons because data in the :class:`~specviz.widgets.workspace.Workspace`
instance is never duplicated; these is a single control of data items, and
the :class:`~specviz.core.models.PlotProxyModel` simply controls the display
of the data items as :class:`~specviz.core.items.PlotDataItem`.

As mentioned, each :class:`~specviz.widgets.workspace.Workspace` can contain
multiple :class:`~specviz.widgets.plotting.PlotWindow`s, and the set of these
:class:`~specviz.widgets.plotting.PlotWindow`s is handled by the `Workspace`s'
`QMdiArea` widget. The
:class:`~specviz.widgets.workspace.Workspace` is also responsible for adding
(:func:`~specviz.widgets.workspace.Workspace.add_plot_window`),
removing (:func:`~specviz.widgets.workspace.Workspace.remove_current_window`),
and providing access to the current (:func:`~specviz.widgets.workspace.Workspace.current_plot_window`),
or entire list of,
:class:`~specviz.widgets.plotting.PlotWindow`s. Workspaces also act as the
source for events raised by interacting with both :class:`~specviz.widgets.plotting.PlotWindow`
items as well as :class:`~specviz.core.items.PlotDataItem`s in the list view
widget.

+--------------------------+--------------------------------------------------------------------------+
| window_activated         | Fired when a single Workspace becomes current.                           |
+--------------------------+--------------------------------------------------------------------------+
| window_closed            | Fired when a Workspace is closed.                                        |
+--------------------------+--------------------------------------------------------------------------+
| current_item_changed     | Proxy signal indicating that an item in the list view has changed.       |
+--------------------------+--------------------------------------------------------------------------+
| current_selected_changed | Fired when the selected item in the list view has changed.               |
+--------------------------+--------------------------------------------------------------------------+
| plot_window_added        | Fired when a new PlotWindow is added to the Workspace's QMdiArea widget. |
+--------------------------+--------------------------------------------------------------------------+
| plot_window_activated    | Fired when a PlotWindow becomes active.                                  |
+--------------------------+--------------------------------------------------------------------------+

:class:`~specviz.widgets.workspace.Workspace`s also contain the methods for providing
the Qt dialogs for
loading data (:func:`~specviz.widgets.workspace.Workspace.load_data`) using the
`specutils` IO infrastructure, as well as
exporting data (:func:`~specviz.widgets.workspace.Workspace._on_export_data`),
and deleting data items (:func:`~specviz.widgets.workspace.Workspace._on_delete_data`).

Plot Windows and Plot Widget
----------------------------

:class:`~specviz.widgets.plotting.PlotWindow`s are implemented as subclasses
of `QMdiSubWindow` Qt objects. On creation, these sub window objects are added
to the :class:`~specviz.widgets.workspace.Workspace`'s `QMdiArea` and exposed
as tabs in the plot window area. Each :class:`~specviz.widgets.plotting.PlotWindow`
contains the set of tools used to interact with the plot directly. This mostly
includes things like changing line colors (which will be reflected in
colored icon next to the data item in the data item list).

:class:`~specviz.widgets.plotting.PlotWindow`s are instantiated by their parent
:class:`~specviz.widgets.workspace.Workspace`, and are passed a reference to the
:class:`~specviz.widgets.workspace.Workspace`'s :class:`~specviz.core.models.DataListModel`.
It is the responsibility of the :class:`~specviz.widgets.plotting.PlotWindow`
(and, more specifically, the :class:`~specviz.widgets.plotting.PlotWindow`'s
:class:`~specviz.widgets.plotting.PlotWidget`) to create the corresponding
:class:`~specviz.core.models.PlotProxyModel` used for that particular
:class:`~specviz.widgets.plotting.PlotWindow` instance. In essence, the
:class:`~specviz.widgets.plotting.PlotWindow` is really a
container for housing the plot tool bar and the :class:`~specviz.widgets.plotting.PlotWidget`,
and generally only contains functionality that doesn't directly involve
manipulating the :class:`~specviz.widgets.plotting.PlotWidget` directly.

The :class:`~specviz.widgets.plotting.PlotWidget` is the plotted representation of
all the :class:`~specviz.core.items.PlotDataItem`s in its internal
:class:`~specviz.core.models.PlotProxyModel`. The widget itself is a subclass
of `PyQtGraph`'s `PlotWidget` object. Anything that affects the visual
representation of the loaded data is done in this class. For instance, operations
like changing the displayed units of the plot are handled here, in which case,
the :class:`~specviz.widgets.plotting.PlotWidget` updates its local
:class:`~specviz.core.items.PlotDataItem` with the new unit information, triggering
 the :class:`~specviz.widgets.plotting.PlotWidget` to re-render.

:class:`~specviz.widgets.plotting.PlotWidget` also handles operations like
adding/removing ROIs to/from a plot, as well as reporting region selection
information for the currently active ROI. In addition, it also contains the
methods for adding (:func:`~specviz.widgets.plotting.PlotWidget.add_plot`) and
removing (:func:`~specviz.widgets.plotting.PlotWidget.remove_plot`)
:class:`~specviz.core.items.PlotDataItem`s, and
responding to changes in their visibility state. The :class:`~specviz.widgets.plotting.PlotWidget`
has several events that other widgets may listen to

+--------------+-------------------------------------------------------------+
| plot_added   | Fired when a `PlotDataItem` has been added to the plot.     |
+--------------+-------------------------------------------------------------+
| plot_removed | Fired when a `PlotDataItem` has been removed from the plot. |
+--------------+-------------------------------------------------------------+
| roi_moved    | Fired when an ROI has been moved on the plot.               |
+--------------+-------------------------------------------------------------+
| roi_removed  | Fired when an ROI has been removed from the plot.           |
+--------------+-------------------------------------------------------------+

Plot Proxy Model and Plot Data Items
------------------------------------

The :class:`~specviz.core.models.PlotProxyModel` is a simple wrapper that
can be used to expose :class:`~specviz.core.items.PlotDataItem`s for use in
:class:`~specviz.widgets.plotting.PlotWindow`s. When a :class:`~specviz.widgets.plotting.PlotWindow`
is created and activated, the parent :class:`~specviz.widgets.workspace.Workspace`
receives a signal and sets the model displayed in the data list view to the
:class:`~specviz.widgets.plotting.PlotWindow`'s :class:`~specviz.core.models.PlotProxyModel`.
The :class:`~specviz.core.models.PlotProxyModel` itself