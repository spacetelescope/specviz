import os
import sys
import traceback
from urllib.parse import urljoin
from multiprocessing import Process, Queue

import pytest

from specviz.app import Application


BOX_PREFIX = 'https://stsci.box.com/shared/static/'

JWST_DATA_FILES = [
    # NIRISS WFSS
    # jw87600017001_02101_00002_nis_x1d_ref.fits
    'fuq1816pljilritjt010un9c0xflxg46.fits',
    # NIRISS SOSS (lvl 2 data)
    # jw10003001002_03101_00001-seg003_nis_x1dints_ref.fits
    'bex0rs8gkqt22sip2z5kvteecutd3czl.fits',
    # NIRSpec Fixed Slit (lvl 2 data)
    # jw00023001001_01101_00001_NRS1_x1d_ref.fits
    '3b01kkv5ndndtja4c7c748mwln7eyt2a.fits',
    # NIRSpec MSA (lvl 2 data)
    # f170lp-g235m_mos_observation-6-c0e0_001_dn_nrs1_mod_x1d_ref.fits
    'v1h9jpg24rusalpui2jpqyldlrqjmv7k.fits',
    # NIRSpec BOTS (bright object time series)  (lvl 2 data)
    # jw84600042001_02101_00001_nrs2_x1dints_ref.fits
    '7yhueeu7yheektf5i48hctocyg9dvfdh.fits',
    # MIRI IFU (lvl 2)
    # jw10001001001_01101_00001_mirifushort_x1d_ref.fits
    'e4c1d8e6prj8e8wpsl1o21w4amnbqj41.fits',
    # MIRI IFU (lvl 3)
    # det_image_ch1-short_x1d_ref.fits
    'bc5vy68irzcgdmuzjpcqoqzvh2qpbc7u.fits',
    # MIRI LRS Slitless time-series  (lvl 2)
    # jw80600012001_02101_00003_mirimage_x1dints_ref.fits
    '6r10ofl8usxqbloen7ostwrudesddyoa.fits',
    # MIRI LRS Fixed-slit time-series   (lvl 2)
    # jw00035001001_01101_00001_MIRIMAGE_x1dints_ref.fits
    '573161xpuzmni12if9dxf0ro1mvx6wy8.fits',
    # MIRI LRS Fixed-slit   (lvl 2)
    # jw00035001001_01101_00001_MIRIMAGE_x1d_ref.fits
    'leyplx2pmh525rsv88lodmtn064uzs68.fits'
    # TODO: add NIRSpec IFU (lvl 2 data)
]

JWST_DATA_PATHS = [urljoin(BOX_PREFIX, name) for name in JWST_DATA_FILES]

jwst_data_test = pytest.mark.skipif(
                    not os.environ.get('JWST_DATA_TEST'),
                    reason='Since these tests run in a subprocess they do not '
                    'play nicely with the fixture that is used for the rest of '
                    'the test suite.')


def run_subprocess_test(callback, *args):
    def run_specviz_subprocess(q, callback, *args):
        try:
            callback(args[0])
        except Exception:
            ex_type, ex_value, tb = sys.exc_info()
            error = ex_type, ex_value, ''.join(traceback.format_tb(tb))
        else:
            error = None
        q.put(error)

    q = Queue()
    # Running multiple subsequent Qt applications in the same process seems to
    # cause segfaults, so we run each specviz instance in a separate process
    p = Process(target=run_specviz_subprocess, args=(q, callback, *args))
    p.start()
    error = q.get()
    p.join()

    if error:
        ex_type, ex_value, tb_str = error
        message = '{} (in subprocess)\n{}'.format(ex_value, tb_str)
        raise ex_type(message)


@jwst_data_test
@pytest.mark.parametrize('url', JWST_DATA_PATHS)
def test_load_jwst_data(url):

    def load_jwst_data(url):
        try:
            spec_app = Application([], skip_splash=True)
            data = spec_app.current_workspace.load_data(url)
            # Basic sanity check to make sure there are data items
            assert len(data) > 0
        finally:
            spec_app.quit()

    run_subprocess_test(load_jwst_data, url)
