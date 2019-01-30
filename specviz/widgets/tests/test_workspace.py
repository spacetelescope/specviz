def test_create_filters(specviz_gui):

    workspace = specviz_gui.add_workspace()
    filters, loader_name_map = workspace._create_loader_filters()

    # Simple sanity test to make sure regression was removed
    assert filters[0] == 'Auto (*)'
    assert loader_name_map['Auto (*)'] is None
