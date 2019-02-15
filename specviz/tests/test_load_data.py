import os
import sys
import traceback
from urllib.parse import urljoin
from multiprocessing import Process, Queue

import pytest

from astropy.io import fits

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
# This is a valid JWST data file, but not one that can be handled by any of the
# specutils loaders (since it does not contain spectral data). It is intended
# to test the fix for the issue reported in
# https://github.com/spacetelescope/specviz/issues/618
BAD_DATA_PATH = urljoin(BOX_PREFIX, '71i9r6k95kodcqoc7urwsywu49x3zwci.fits')
HST_COS_PATH = urljoin(BOX_PREFIX, 'nh3ze6di0lpitz3nn2coj0vgwd9x7mnp.fits')

jwst_data_test = pytest.mark.skipif(
                    not os.environ.get('JWST_DATA_TEST'),
                    reason='Since these tests run in a subprocess they do not '
                    'play nicely with the fixture that is used for the rest of '
                    'the test suite.')


def run_subprocess_test(run_test, *args, callback=None, **app_kwargs):
    def run_specviz_subprocess(q, run_test, *args):
        try:
            app = Application([], skip_splash=True, **app_kwargs)
            if run_test is not None:
                run_test(app, args[0])
        except Exception:
            ex_type, ex_value, tb = sys.exc_info()
            error = ex_type, ex_value, ''.join(traceback.format_tb(tb))
        else:
            error = None
        finally:
            app.quit()

        q.put(error)

    callback = callback or run_specviz_subprocess

    q = Queue()
    # Running multiple subsequent Qt applications in the same process seems to
    # cause segfaults, so we run each specviz instance in a separate process
    p = Process(target=callback, args=(q, run_test, *args))
    p.start()
    error = q.get()
    p.join()

    if error:
        ex_type, ex_value, tb_str = error
        message = '{} (in subprocess)\n{}'.format(ex_value, tb_str)
        raise ex_type(message)


def download_test_data(tmpdir, url):
    fname = str(tmpdir.join('test_data.fits'))
    with fits.open(url) as hdulist:
        hdulist.writeto(fname)
    return fname


@jwst_data_test
@pytest.mark.parametrize('url', JWST_DATA_PATHS)
def test_load_jwst_data(url):

    def load_jwst_data(spec_app, url):
        # Use loader auto-detection here
        data = spec_app.current_workspace.load_data_from_file(url, multi_select=False)
        # Basic sanity check to make sure there are data items
        assert len(data) > 0

    run_subprocess_test(load_jwst_data, url)


@jwst_data_test
def test_valid_loader(tmpdir):
    """
    Explicitly request to use the appropriate loader for a HST/COS data file
    """

    def use_valid_loader(spec_app, tmpdir):
        fname = download_test_data(tmpdir, HST_COS_PATH)
        spec_app.current_workspace.load_data_from_file(fname,
                                                       file_loader='HST/COS',
                                                       multi_select=False)

    run_subprocess_test(use_valid_loader, tmpdir)


@jwst_data_test
def test_invalid_data_file(tmpdir):
    """
    Try to open a non-spectral FITS file. It shouldn't load.

    This is to make sure we get a reasonable error from the loader itself
    rather than an unexpected error later on.
    """

    def open_invalid_data(spec_app, tmpdir):
        fname = download_test_data(tmpdir, BAD_DATA_PATH)
        with pytest.raises(IOError) as err:
            spec_app.current_workspace.load_data_from_file(fname,
                                                           multi_select=False)
            assert err.msg.startswith('Could not find appropriate loader')

    run_subprocess_test(open_invalid_data, tmpdir)


@jwst_data_test
@pytest.mark.parametrize('url', [JWST_DATA_PATHS[0], BAD_DATA_PATH])
def test_invalid_loader(url, tmpdir):
    """
    Try to open both a valid data file with the wrong loader and an invalid
    data file with any specific loader (rather than auto-identify).

    We expect to get a reasonable error.
    """

    def use_wrong_loader(spec_app, tmpdir):
        fname = download_test_data(tmpdir, url)
        with pytest.raises(IOError) as err:
            # Using the HST/COS loader is not appropriate for a JWST data file
            spec_app.current_workspace.load_data_from_file(fname,
                                                           file_loader='HST/COS',
                                                           multi_select=False)
            assert err.msg.startswith(
                 'Given file can not be processed as specified file format')
            assert 'HST/COS' in err.msg

    run_subprocess_test(use_wrong_loader, tmpdir)


@jwst_data_test
def test_nonexistent_loader(tmpdir):
    """
    Try to specify a loader that doesn't exist.
    """

    def use_valid_loader(spec_app, tmpdir):
        fname = download_test_data(tmpdir, HST_COS_PATH)
        with pytest.raises(IOError) as err:
            spec_app.current_workspace.load_data_from_file(fname,
                                                           file_loader='FAKE',
                                                           multi_select=False)
            assert err.msg.startswith(
                 'Given file can not be processed as specified file format')
            assert 'FAKE' in err.msg

    run_subprocess_test(use_valid_loader, tmpdir)


@jwst_data_test
def test_load_data_command_line(tmpdir):
    """
    Test to simulate the case where a data file is provided on the command line
    """

    def callback(q, run_test, *args):
        fname = download_test_data(args[0], JWST_DATA_PATHS[0])

        try:
            app = Application([], skip_splash=True, file_path=fname,
                              load_all=True)
        except Exception:
            ex_type, ex_value, tb = sys.exc_info()
            error = ex_type, ex_value, ''.join(traceback.format_tb(tb))
        else:
            error = None
        finally:
            app.quit()

        q.put(error)

    run_subprocess_test(None, tmpdir, callback=callback)
