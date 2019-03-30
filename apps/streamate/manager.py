# -*- coding: utf-8 -*-
import logging
from itertools import chain

from concurrent import futures

from apps.common.manager import Manager
from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException
from apps.streamate import packer
from apps.streamate import epggrabber
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

    def hire_grabbers(self, *grabber_names):
        grabbers = []
        for name in grabber_names:
            name = name.capitalize()
            if name in self.__epg_grabber_classes:
                grabbers.append(self.__epg_grabber_classes[name](fetchers.hire_fetcher(**{k.lower(): v for k, v in self.config['FETCHER'].iteritems()})))
        if grabber_names and len(grabbers) < 1:
            raise KeyError('There is no grabber named : %s' % ', '.join(grabber_names))
        if len(grabbers) < 1:
            grabbers = [class_(fetchers.hire_fetcher(**{k.lower(): v for k, v in self.config['FETCHER'].iteritems()})) for class_ in self.__epg_grabber_classes.itervalues()]
        return grabbers

    def hire_streamers(self, *streamer_names):
        classes = []
        for name in streamer_names:
            if name.capitalize() in self.__streamer_classes:
                classes.append(self.__streamer_classes[name.capitalize()])
        if streamer_names and len(classes) < 1:
            raise KeyError('There is no streamer named : %s' % ', '.join(streamer_names))
        if len(classes) < 1:
            classes = [class_ for class_ in self.__streamer_classes.itervalues()]
        streamers = []
        for class_ in classes:
            config = self.config['STREAMERS'][class_.__name__]
            config['CHANNELS'] = self.config['CHANNELS']
            streamers.append(class_(config, fetchers.hire_fetcher(**{k.lower(): v for k, v in self.config['FETCHER'].iteritems()})))
        return streamers

    def _order_resource(self, streamer, query):
        return streamer.get_resource(ud.Url(ud.unquote(query.get('url'))))

    def _order_channels(self, streamer, query):
        return streamer.get_channels()

    def _order_streaming(self, streamer, query):
        return streamer.streaming

    def _order_m3u(self, streamer, query):
        return packer.pack_m3u(streamer.get_channels(), query.get('ffmpeg'))

    def order_all_m3u(self, query):
        with futures.ThreadPoolExecutor() as exe:
            generators = exe.map(lambda streamer: streamer.get_channels(), self.hire_streamers())
            return packer.pack_m3u(chain.from_iterable(generators), query.get('ffmpeg'))

    def order_all_epg(self, query):
        grabbers = self.hire_grabbers(*query.getlist('grabber'))
        return packer.pack_epg(epggrabber.get_epg(self.config['CHANNELS'], grabbers, query.get('days', default=1, type=int)))

    def _order_test(self, streamer, query):
        return streamer.get_internal_epg(query.get('ch'), query.get('days', type=int))


    def request(self, streamer, order, query):
        # type: (str, Type[Dict[str, Union[List[str], str]]]) -> ?
        try:
            self.__streamer_classes[streamer.capitalize()]
        except KeyError:
            raise MyFlaskException("There is no streamer : '%s'", streamer.capitalize())
        instance = self.hire_streamers(streamer.capitalize())[0]
        try:
            function = getattr(self, '_order_%s' % order)
        except AttributeError as e:
            log.error(e.message)
            return "there is no such order : '%s'" % order
        data = function(instance, query)
        return data
