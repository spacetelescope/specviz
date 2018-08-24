from qtpy.QtWidgets import QMenu, QAction


def dict_to_menu(parent, menu_dict, menu_widget=None):
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
