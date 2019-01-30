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


