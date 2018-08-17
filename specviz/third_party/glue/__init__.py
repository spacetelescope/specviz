def setup():
    from glue.config import qt_client
    from .viewer import SpecvizViewer
    from .viewer_single_spectrum import SpecvizSingleDataViewer
    qt_client.add(SpecvizViewer)
    qt_client.add(SpecvizSingleDataViewer)
