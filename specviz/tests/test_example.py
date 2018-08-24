def test_deprecation():
    import warnings
    warnings.warn(
        "This is deprecated, but shouldn't raise an exception, unless "
        "enable_deprecations_as_exceptions() called from conftest.py",
        DeprecationWarning)
