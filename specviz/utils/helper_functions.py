from astropy import units as u


def format_float_text(value):
    v = value
    if isinstance(v, u.Quantity):
        v = value.value
    elif isinstance(v, str):
        v = float(value)

    if 0.001 <= abs(v) <= 1000 or abs(v) == 0.0:
        return "{0:.3f}".format(value)
    else:
        return "{0:.3e}".format(value)
