Developer Documentation
=======================

This set of documentation focuses on the structure of SpecViz, its various
pieces, and how they work together.

Data Model
----------

The central piece of SpecViz is the internal Qt data model expressed in the
:class:`~specviz.core.models.DataListModel` class. It is responsible
for maintaining the collection of :class:`~specutils.Spectrum1D` objects and
exposing them as Qt :class:`specviz.core.items.DataItem` objects.

In the context of SpecViz, the :class:`~specutils.Spectrum1D` is considered
immutable. In a similar sense, :class:`specviz.core.items.DataItem` is only a
Qt interface to an *instance* of the :class:`~specutils.Spectrum1D` class. As
such, it is possible to change which :class:`~specutils.Spectrum1D` the
:class:`specviz.core.items.DataItem` contains, but otherwise exposes no other
means to mutate the item.

While SpecViz contains Qt view widgets that expose
:class:`~specviz.core.models.DataListModel` items (e.g. `QListView`), this is
generally not done directly. Instead, a proxy model (:class:`~specviz.core.models.PlotProxyModel`)
is used to wrap and expose the :class:`~specviz.core.items.DataItem` items as
:class:`~specviz.core.items.PlotDataItem` items. These are fundamentally
different from the :class:`specviz.core.items.DataItem`s in that they contain
mutable attributes that determine how the :class:`specviz.core.items.DataItem`
they contain will be expressed in SpecViz. This ranges from whether or not the
item is hidden, what its current plot color is, what its currently user-defined
name is, etc.

Application and Workspaces
--------------------------

