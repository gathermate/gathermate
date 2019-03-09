# -*- coding: utf-8 -*-
import logging

from apps.common.manager import Manager
from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException

log = logging.getLogger(__name__)

def hire_manager(config):
    # type: (flask.config.Config, Text) -> Manager
    return StreamManager(config)


class StreamManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(StreamManager, self).__init__(config)
        self.__streamer_classes = self._register_modules('apps.streamate.streamers', 'Streamer')

    def _order_resource(self, streamer, query):
        return streamer.get_resource(ud.Url(ud.unquote(query.get('url'))))

    def _order_channels(self, streamer, query):
        return streamer.get_channels(int(query.get('page')))

    def _order_info(self, streamer, query):
        return 'info'

    def _order_streaming(self, streamer, query):
        return streamer.streaming

    def request(self, streamer, order, query):
        # type: (str, Type[Dict[str, Union[List[str], str]]]) -> ?
        try:
            class_ = self.__streamer_classes[streamer.capitalize()]
        except KeyError as e:
            log.error(e.message)
            return "There is no streamer : '%s'" % streamer
        instance = class_(self.config)
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
