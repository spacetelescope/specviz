from qtpy.QtWidgets import QMenu, QAction


def dict_to_menu(parent, menu_dict, menu_widget=None):
    """
    Build a QMenu based on a dictionary.

    Parameters
    ----------
    parent : QWidget
        The parent widget where the menu will be used
    menu_dict : dict
        A dictionary describing the menu. The keys of the dictionary should be
        the name of the menu items, while the value should be a callable function
        or a tuple of ('checkable', callable function) if the menu item should
        be checkable.
    menu_widget : QMenu, optional
        An existing QMenu instance if the entries are to be added to an existing
        menu.

    Returns
    -------
    QMenu
        The menu to add the entries to.

    """
    if not menu_widget:
        menu_widget = QMenu(parent)
    for k, v in menu_dict.items():
        if isinstance(v, dict):
            new_menu = menu_widget.addMenu(k)
            dict_to_menu(v, menu_widget=new_menu)
        else:
            act = QAction(k, menu_widget)

            if isinstance(v, list):
                if v[0] == 'checkable':
                    v = v[1]
                    act.setCheckable(True)
                    act.setChecked(False)

            act.triggered.connect(v)
            menu_widget.addAction(act)
    return menu_widget
