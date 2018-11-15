import shutil
import urllib.request

from specviz.plugins.loader_wizard.loader_wizard import (ASCIIImportWizard,
                                                         simplify_arrays,
                                                         parse_ascii)


def test_loader_wizard(tmpdir, qtbot):

    tmpfile = str(tmpdir.join('example.fits'))

    data_url = 'https://stsci.app.box.com/s/zz2vgbreuzhjtel0d5u96r30oofolod7/file/345743002081'
    with urllib.request.urlopen(data_url) as response:
        with open(tmpfile, 'wb') as handle:
            shutil.copyfileobj(response, handle)

    arrays = simplify_arrays(parse_ascii(tmpfile, 'format = "ascii"'))
    widget = ASCIIImportWizard(tmpfile, arrays)

    qtbot.addWidget(widget)

    widget.show()
    # TODO: remove for automated tests
    qtbot.stopForInteraction()
