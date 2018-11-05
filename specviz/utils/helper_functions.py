from astropy import units as u
from specutils.spectra.spectral_region import SpectralRegion


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


def pos_to_spectral_region(pos):
    """
    Vet input region position and construct
    a `~specutils.utils.SpectralRegion`.
    Parameters
    ----------
    pos : `~astropy.units.Quantity`
        A tuple `~astropy.units.Quantity` with
        (min, max) range of roi.

    Returns
    -------
    None or `~specutils.utils.SpectralRegion`
    """
    if not isinstance(pos, u.Quantity):
        return None
    elif pos.unit == u.Unit("") or \
            pos[0] == pos[1]:
        return None
    elif pos[0] > pos[1]:
        pos = [pos[1], pos[0]] * pos.unit
    return SpectralRegion(*pos)


def check_region_unit_compatibility(spec, region):
    spec_unit = spec.spectral_axis.unit
    if region.lower is not None:
        region_unit = region.lower.unit
    elif region.upper is not None:
        region_unit = region.upper.unit
    else:
        return False
    return spec_unit.is_equivalent(region_unit)


def clip_region(spectrum, region):
    # If the region is out of data range return None:
    if region.lower > spectrum.spectral_axis.max() or \
            region.upper < spectrum.spectral_axis.min():
        return None

    # Clip region. There is currently no way to update
    # SpectralRegion lower and upper so we have to create
    # a new object here.
    lower = max(region.lower, spectrum.spectral_axis.min())
    upper = min(region.upper, spectrum.spectral_axis.max())

    return SpectralRegion(lower, upper)

