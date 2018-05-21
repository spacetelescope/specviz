import logging

import gevent
import msgpack
import json
from zerorpc import Client, Puller, Pusher, Subscriber
from zmq.error import ZMQError

from .core.items import DataItem


class SubscriberAPI():
    def __init__(self, client_ip):
        # Setup pusher service
        self.client = Client()
        self.client.connect(client_ip)

    def data_loaded(self, identifier):
        """
        A message indicating that a data object has been loaded into the store
        with the given identifier.
        """
        value_dict = self.client.query_data(identifier,
                                            ['flux', 'wavelength', 'unit'])

        data = DataItem(name=value_dict['name'],
                        identifier=value_dict['identifier'],
                        spectral_axis=['spectral_axis'],
                        spectral_axis_unit=['spectral_axis_unit'],
                        data=value_dict['flux'],
                        unit=value_dict['unit'])

    def data_unloaded(self, identifier):
        pass


def launch(server_ip=None, client_ip=None):
    logging.info("Starting services...")

    server_ip = server_ip or "tcp://127.0.0.1:4242"
    client_ip = client_ip or "tcp://127.0.0.1:4243"

    # Setup the subscriber service
    sub_api = SubscriberAPI(client_ip)
    subscriber = Subscriber(sub_api)

    try:
        subscriber.bind(server_ip)
    except ZMQError:
        pass

    gevent.spawn(subscriber.run)

    logging.info(
        "Client is now sending on %s and listening on %s.",
        client_ip, server_ip)

    trigger = gevent.event.Event()
    trigger.wait(1)
    sub_api.client.load_data(
        "/Users/nearl/projects/specutils/specutils/tests/data/L5g_0355+11_Cruz09.fits",
        "wcs1d-fits")
    trigger.wait(1)
    # print(sub_api.client.query_data('blah', ['blah']))

    # Attempt testing whether fuction was added to server object
    # sub_api.client.testing("This is a test on the server")
    # sub_api.client.smooth_data(list(range(10)))
    # sub_api.client.load_data_from_path('/home/nmearl/Downloads/Transcript.txt', '*')
