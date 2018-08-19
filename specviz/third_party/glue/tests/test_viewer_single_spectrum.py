import numpy as np
from astropy.wcs import WCS

from glue.app.qt import GlueApplication

from glue.core import Data
from glue.core.component import Component
from glue.core.coordinates import WCSCoordinates

from ..viewer_single_spectrum import SpecvizSingleDataViewer


class TestSpecvizSingleDataViewer(object):

    def setup_method(self, method):

        # Set up simple spectral WCS
        wcs = WCS(naxis=1)
        wcs.wcs.ctype = ['VELO-LSR']
        wcs.wcs.set()

        # Set up glue Coordinates object
        coords = WCSCoordinates(wcs=wcs)

        self.data = Data(label='spectrum', coords=coords)

        # FIXME: there should be an easier way to do this in glue
        self.data.add_component(Component(np.array([3.4, 2.3, -1.1, 0.3]), units='Jy'), 'x')
        self.data.add_component(Component(np.array([3.2, 3.3, 3.4, 3.5]), units='Jy'), 'y')

        self.app = GlueApplication()
        self.session = self.app.session
        self.hub = self.session.hub

        self.data_collection = self.session.data_collection
        self.data_collection.append(self.data)

    def test_init_viewer(self):
        self.app.new_data_viewer(SpecvizSingleDataViewer)

    def test_add_data(self):
        viewer = self.app.new_data_viewer(SpecvizSingleDataViewer)
        viewer.add_data(self.data)
        assert viewer.layers[0].plot_data_item.visible

    def test_define_subset(self):
        viewer = self.app.new_data_viewer(SpecvizSingleDataViewer)
        viewer.add_data(self.data)
        self.data_collection.new_subset_group(subset_state=self.data.id['x'] > 0, label='Subset')
        assert viewer.layers[0].plot_data_item.visible
        assert viewer.layers[0].plot_data_item.zorder == 1
        assert viewer.layers[1].plot_data_item.visible
        assert viewer.layers[1].plot_data_item.zorder == 2
