def setup():
    from glue.config import qt_client
    from .viewer import SpecvizDataViewer
    qt_client.add(SpecvizDataViewer)
