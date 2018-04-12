import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS, WCSSUB_SPECTRAL

UNIT_FIXES = {
    'COUNTS SEC-1 METER-1': u.count / u.s / u.m,
    'MICRONS': u.micron,
    'HZ': u.Hz,
    'ergs/cm^2/s': u.erg / u.cm ** 2 / u.s,
    '(COUNTS SEC-1 METER-1)**2': (u.count / u.s / u.m) ** 2
}


def parse_unit(unit):
    unit = UNIT_FIXES.get(unit, unit)
    unit = u.Unit(unit, parse_strict='silent')
    return unit


def parse_fits(filename):

    parsed_hdus = {}

    with fits.open(filename) as hdulist:

        for ihdu, hdu in enumerate(hdulist):

            parsed_hdu = {}

            # Check for spectral WCS
            try:
                wcs = WCS(hdu.header)
            except:
                wcs = WCS(naxis=1)

            if wcs.wcs.spec >= 0:

                # Extract spectral WCS
                wcs_spec = wcs.sub([WCSSUB_SPECTRAL])

                # Find spectral coordinates
                parsed_hdu['WCS::Spectral'] = {'data': wcs_spec,
                                               'ndim': 1,
                                               'unit': wcs_spec.wcs.cunit[0]}

            if isinstance(hdu, (fits.PrimaryHDU, fits.ImageHDU)):

                if 'BUNIT' in hdu.header:
                    unit = parse_unit(hdu.header['BUNIT'])
                else:
                    unit = None

                if hdu.data is not None and hdu.data.size > 0:
                    parsed_hdu[hdu.name] = {'data': hdu.data,
                                            'ndim': hdu.data.ndim,
                                            'shape': hdu.data.shape,
                                            'unit': unit,
                                            'index': ihdu}

            elif isinstance(hdu, (fits.TableHDU, fits.BinTableHDU)):

                for column in hdu.columns:

                    if column.unit is None:
                        unit = None
                    else:
                        unit = parse_unit(column.unit)

                    data = hdu.data[column.name]

                    # If the parsed data is of type string, ignore this column
                    if isinstance(data, np.chararray):
                        continue

                    parsed_hdu[column.name] = {'data': data.flatten(),
                                               'ndim': data.ndim,
                                               'shape': data.shape,
                                               'unit': unit,
                                               'index': ihdu}

            if len(parsed_hdu) > 0:
                hdu_name = hdu.name or 'HDU {0}'.format(ihdu)
                parsed_hdus[hdu_name] = parsed_hdu

    return parsed_hdus


def simplify_arrays(datasets):

    for dataset in datasets.values():
        for component in dataset.values():
            if isinstance(component['data'], WCS):
                continue
            shape = component['data'].shape
            if np.product(shape) == np.max(shape):
                component['data'] = component['data'].ravel()
                component['ndim'] = component['data'].ndim
                component['shape'] = component['data'].shape
    return datasets


if __name__ == "__main__":

    import glob

    for filename in glob.glob('spectra/3000030_1_sed.fits'):
        print('-' * 72)
        print(filename)
        print('-' * 72)
        hdus = parse_fits(filename)
        hdus = simplify_arrays(hdus)
        for name in hdus:
            print('HDU:', name)
            hdu = hdus[name]
            for array_name in hdu:
                array = hdu[array_name]
                print('  Array:', array_name)
                print('    data:', array['data'].min(), array['data'].max())
                print('    ndim:', array['ndim'])
                print('    shape:', array['shape'])
                print('    unit:', array['unit'])
