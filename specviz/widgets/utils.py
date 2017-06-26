import os
from contextlib import contextmanager

QWIDGETSIZE_MAX = ((1 << 24) - 1)
ICON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                         '..', 'data', 'qt', 'resources'))
UI_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                       '..', 'data', 'qt', 'ui'))


@contextmanager
def updates_disabled(widget):
    """Disable QWidget updates (using QWidget.setUpdatesEnabled)
    """
    old_state = widget.updatesEnabled()
    widget.setUpdatesEnabled(False)
    try:
        yield
    finally:
        widget.setUpdatesEnabled(old_state)