# -*- coding: utf-8 -*-
import logging
from itertools import chain

from concurrent import futures

from apps.common.manager import Manager
from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException
from apps.streamate import packer
from apps.common import fetchers

log = logging.getLogger(__name__)

def hire_manager(config):
    # type: (flask.config.Config, Text) -> Manager
    return StreamManager(config)


class StreamManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(StreamManager, self).__init__(config)
        self.__streamer_classes = self._register_modules('apps.streamate.streamers', 'Streamer')
        self.__epg_grabber_classes = self._register_modules('apps.streamate.epggrabbers', 'EpgGrabber')

    def _order_resource(self, streamer, query):
        return streamer.get_resource(ud.Url(ud.unquote(query.get('url'))))

    def _order_channels(self, streamer, query):
        return streamer.get_channels()

    def _order_info(self, streamer, query):
        return 'info'

    def _order_streaming(self, streamer, query):
        return streamer.streaming

    def _order_m3u(self, streamer, query):
        return packer.pack_m3u(streamer.get_channels())

    def _order_epg(self, streamer, query):
        grabbers = []
        for grabber in query.getlist('grabber'):
            try:
                class_ = self.__epg_grabber_classes[grabber.capitalize()]
                grabbers.append(class_(fetchers.hire_fetcher(self.config['FETCHER'])))
            except KeyError as e:
                log.error(e.message)
        return packer.pack_epg(streamer.get_epg(grabbers, query.get('days', default=1, type=int)))

    def order_all_m3u(self, query):
        with futures.ThreadPoolExecutor(max_workers=2) as exe:
            generators = exe.map(lambda class_: class_(self.config).get_channels(), self.__streamer_classes.itervalues())
            return packer.pack_m3u(chain.from_iterable(generators))

    def request(self, streamer, order, query):
        # type: (str, Type[Dict[str, Union[List[str], str]]]) -> ?
        try:
            class_ = self.__streamer_classes[streamer.capitalize()]
        except KeyError as e:
            log.error(e.message)
            return "There is no streamer : '%s'" % streamer
        instance = class_(self.config['STREAMERS'][streamer.capitalize()], fetchers.hire_fetcher(self.config['FETCHER']))
        #fetchers_log = logging.getLogger('apps.common.fetchers')
        #fetchers_log.setLevel('INFO')
        function = None
        try:
            function = getattr(self, '_order_%s' % order)
        except AttributeError as e:
            log.error(e.message)
            return "there is no such order : '%s'" % order
        data = function(instance, query)
        #fetchers_log.setLevel(self.config.get('LOG_LEVEL'))
        return data
