# -*- coding: utf-8 -*-

import logging
from itertools import chain
import copy

from concurrent import futures

from apps.common.manager import Manager
from apps.common import urldealer as ud
from apps.common.exceptions import GathermateException
from apps.streamate import packer
from apps.streamate import epggrabber

log = logging.getLogger()

def hire_manager(config):
    return StreamManager(config)


class StreamManager(Manager):

    def __init__(self, config):
        super(StreamManager, self).__init__(config)
        self.__streamer_classes = self._register_modules('apps.streamate.streamers', 'Streamer')
        self.__epg_grabber_classes = self._register_modules('apps.streamate.epggrabbers', 'EpgGrabber')

    def hire_grabbers(self, *grabber_names):
        grabbers = []
        for name in grabber_names:
            name = name.capitalize()
            if name in self.__epg_grabber_classes:
                grabbers.append(
                    self.__epg_grabber_classes[name](self._hire_fetcher()))
        if grabber_names and len(grabbers) < 1:
            raise KeyError('There is no grabber named : %s' % ', '.join(grabber_names))
        if len(grabbers) < 1:
            grabbers = [class_(self._hire_fetcher()) for class_ in self.__epg_grabber_classes.itervalues()]
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
            streamers.append(class_(
                self._hire_fetcher(),
                mapped_channels=self.config['CHANNELS'],
                **{k.lower(): v for k, v in self.config['STREAMERS'][class_.__name__].iteritems()}
                ))
        return streamers

    def _order_resource(self, streamer, query):
        return streamer.get_resource(ud.Url(ud.unquote(query.get('url'))))

    def _order_channels(self, streamer, query):
        return packer.pack_channels(streamer, self.config['CHANNELS'])

    def _order_streaming(self, streamer, query):
        return streamer.streaming

    def _order_m3u(self, streamer, query):
        return packer.pack_m3u(streamer, self.config['CHANNELS'], query.get('ffmpeg'))

    def order_all_m3u(self, query):
        with futures.ThreadPoolExecutor() as exe:
            generators = exe.map(lambda streamer: streamer.get_channels(), self.hire_streamers())
            return packer.pack_m3u(chain.from_iterable(generators), query.get('ffmpeg'))

    def order_all_epg(self, query):
        grabbers = self.hire_grabbers(*query.getlist('grabber'))
        return packer.pack_epg(epggrabber.get_epg(copy.deepcopy(self.config['CHANNELS']), grabbers, query.get('days', default=1, type=int)))

    def request(self, streamer, order, query):
        try:
            self.__streamer_classes[streamer.capitalize()]
        except KeyError:
            raise GathermateException("There is no streamer : '%s'", streamer.capitalize())
        instance = self.hire_streamers(streamer.capitalize())[0]
        try:
            function = getattr(self, '_order_%s' % order)
        except AttributeError as e:
            log.error(e.message)
            return "there is no such order : '%s'" % order
        data = function(instance, query)
        return data
