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


def _parse_unit(unit):
    unit = UNIT_FIXES.get(unit, unit)
    unit = u.Unit(unit, parse_strict='silent')
    return unit

def parse_fits(filename):

    parsed_hdus = {}

    with fits.open(filename) as hdulist:

        for hdu in hdulist:

            parsed_hdu = {}

            # Check for spectral WCS
            try:
                wcs = WCS(hdu.header)
            except:
                wcs = WCS(naxis=1)

            if wcs.wcs.spec >= 0:

                # Extract spectral WCS
                wcs_spec = wcs.sub([WCSSUB_SPECTRAL])

                # Find shape of data along spectral axis
                n_spec = hdu.data.shape[hdu.data.ndim - 1 - wcs.wcs.spec]

                # Find spectral coordinates
                pix = np.arange(n_spec)
                parsed_hdu['WCS::Spectral'] = {'data': wcs_spec.all_pix2world(pix, 0)[0],
                                               'ndim': 1,
                                               'shape': (n_spec,),
                                               'unit': wcs_spec.wcs.cunit[0]}

            if isinstance(hdu, (fits.PrimaryHDU, fits.ImageHDU)):

                if 'BUNIT' in hdu.header:
                    unit = _parse_unit(hdu.header['BUNIT'])
                else:
                    unit = None

                if hdu.data is not None and hdu.data.size > 0:
                    parsed_hdu[hdu.name] = {'data': hdu.data,
                                            'ndim': hdu.data.ndim,
                                            'shape': hdu.data.shape,
                                            'unit': unit}

            elif isinstance(hdu, (fits.TableHDU, fits.BinTableHDU)):

                for column in hdu.columns:

                    print(column.unit)

                    if column.unit is None:
                        unit = None
                    else:
                        unit = _parse_unit(column.unit)

                    data = hdu.data[column.name]

                    parsed_hdu[column.name] = {'data': data,
                                               'ndim': data.ndim,
                                               'shape': data.shape,
                                               'unit': unit}

            if len(parsed_hdu) > 0:
                parsed_hdus[hdu.name] = parsed_hdu

    return parsed_hdus


def simplify_arrays(datasets):

    for dataset in datasets.values():
        for array in dataset.values():
            shape = array['data'].shape
            if np.product(shape) == np.max(shape):
                array['data'] = array['data'].ravel()
                array['ndim'] = array['data'].ndim
                array['shape'] = array['data'].shape
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
