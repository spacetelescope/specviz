def setup():
    from glue.config import qt_client
    from .viewer import SpecvizViewer
    qt_client.add(SpecvizViewer)
