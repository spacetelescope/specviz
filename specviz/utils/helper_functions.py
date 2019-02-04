from astropy import units as u


def format_float_text(value):
    """
    Auto-format a floating point value as text, automatically choosing
    scientific or floating-point notation as appropriate.

    Parameters
    ----------
    value : `float` or `~astropy.units.Quantity`
        The value to format.

    Returns
    -------
    str
        The formatted string.
    """
    v = value
    if isinstance(v, u.Quantity):
        v = value.value
    elif isinstance(v, str):
        v = float(value)

    if 0.001 <= abs(v) <= 1000 or abs(v) == 0.0:
        return "{0:.3f}".format(value)
    else:
        return "{0:.3e}".format(value)
