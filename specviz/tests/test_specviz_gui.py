def test_spec_gui(specviz_gui):
    """
    Generic test to ensure the pytest fixture is properly feeding an instance
    of the specviz application.
    """
    assert specviz_gui is not None
