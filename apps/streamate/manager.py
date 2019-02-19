# -*- coding: utf-8 -*-
import logging

from apps.common.manager import Manager
from apps.common import fetchers
from apps.common import toolbox as tb
from apps.common import urldealer as ud

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
        url = ud.Url(ud.unquote(query.get('resource')))
        return streamer.get_resource(url)

    def _order_channels(self, streamer, query):
        return streamer.get_channels()

    def _order_media(self, streamer, query):
        url = ud.Url(ud.unquote(query.get('media')))
        cid = query.get('cid')
        return streamer.get_media(cid, url)

    def _order_playlist(self, streamer, query):
        url = ud.Url(ud.unquote(query.get('list')))
        cid = query.get('cid')
        return streamer.get_playlist(cid, url)

    def _order_streamlist(self, streamer, query):
        cid = query.get('cid')
        return streamer.get_streamlist(cid)

    @tb.timeit
    def _get_data(self, order, streamer, query):
        data = getattr(self, '_order_%s' % order)(streamer, query)
        return data

    def request(self, streamer, order, query):
        # type: (str, Type[Dict[str, Union[List[str], str]]]) -> ?
        #logging.getLogger('apps.common.fetchers').setLevel('INFO')
        try:
            streamer = self.__streamer_classes[streamer.capitalize()](self.config)
        except KeyError:
            msg = "There is no streamer : %s" % streamer
            log.error(msg)
            return msg
        return self._get_data(order, streamer, query)


