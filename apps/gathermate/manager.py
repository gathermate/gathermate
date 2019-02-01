# -*- coding: utf-8 -*-

import logging as log

import packer
import gatherer as gtr
from apps.common import fetchers
from apps.common.exceptions import MyFlaskException
from apps.common import toolbox as tb
from apps.common import urldealer as ud
from apps.common.manager import Manager

def hire_manager(config):
    # type: (flask.config.Config) -> GathermateManager
    packer.ACCEPTED_EXT = config.get('ACCEPTED_EXT', [])
    return GathermateManager(config)


class GathermateManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(GathermateManager, self).__init__(config)
        gatherers = self._register_modules('apps.gathermate.gatherers', 'Gatherer', parent_class=gtr.Gatherer)
        self.__gatherer_classes = {ud.URL(class_.URL).hostname: class_ for name, class_ in gatherers.iteritems()}

    def _hire_gatherer(self, target):
        # type: (urldealer.URL) -> Type[gatherer.Gatherer]
        host = target.hostname if target.hostname else target.netloc
        if not host:
            raise MyFlaskException('Target URL is wrong : %s' % target.text)
        try:
            class_ = self.__gatherer_classes[host]
        except KeyError:
            MyFlaskException.trace_error()
            class_ = self._find_gatherer(host)
        log.debug("%s class matches with [%s].", class_.__name__, target.text)
        return self._train_gatherer(class_, self.config.get('GATHERERS'))

    def _find_gatherer(self, alias):
        # type: (str) -> Type[gatherer.Gatherer]
        for host, class_ in self.__gatherer_classes.iteritems():
            if alias in host:
                log.debug("%s class matches with [%s].", class_.__name__, alias)
                return class_
        raise MyFlaskException('There is no class associate with : {}'.format(alias))

    def _train_gatherer(self, class_, config):
        # type: (Type[gatherer.Gatherer], Dict[str, Dict[str, Optional[bool, str, int, List[str]]]])
        # -> Type[gatherer.Gatherer]
        instance_config = self._get_default_config(class_.__name__, config)
        gatherer = class_(instance_config, fetchers.hire_fetcher(self.config))
        log.debug("%s instance has been created.", type(gatherer).__name__)
        return gatherer

    def _get_default_config(self, name, config):
        # type: (str, Dict[str, Dict[str, Optional[bool, str, int, List[str]]]])
        # -> Dict[str, Dict[str, Optional[bool, str, int, List[str]]]]
        default_config = {
            'ENCODING': 'utf-8',
            'RSS_WANT': self.config.get('RSS_WANT', []),
            'RSS_AGGRESSIVE': self.config.get('RSS_AGGRESSIVE', False),
            'RSS_ASYNC': self.config.get('RSS_ASYNC', False),
            'RSS_WORKERS': self.config.get('RSS_WORKERS', 1),
            'RSS_LENGTH': self.config.get('RSS_LENGTH', 5),
        }
        if config.get(name, None):
            default_config.update(config.get(name))
        return default_config

    def _order_rss(self, target, query):
        # type: (urldealer.URL, werkzeug.datastructures.MultiDict) -> str
        gatherer = self._hire_gatherer(target)
        gatherer.isRSS = True
        length = query.get('length', None, type=int)
        if length is not None:
            gatherer.length = length
        listing = gatherer.parse_list(target)
        return packer.pack_rss(gatherer.parse_items(listing))

    def _order_item(self, target, query):
        # type: (urldealer.URL, werkzeug.datastructures.MultiDict)
        # -> List[Dict[str, Union[str, unicode]]]
        gatherer = self._hire_gatherer(target)
        items = gatherer.parse_item(target)
        return packer.pack_item(items)

    def _order_list(self, target, query):
        # type: (urldealer.URL, werkzeug.datastructures.MultiDict)
        # -> Dict[str, Union[int, List[Tuple[int, Dict[str, Union[int, str, unicode]]]]]]
        gatherer = self._hire_gatherer(target)
        listing = gatherer.parse_list(target)
        return packer.pack_list(listing)

    def _order_down(self, target, query):
        # type: (urldealer.URL, werkzeug.datastructures.MultiDict) -> fetchers.Response
        ticket = query.get('ticket')
        if ticket:
            ticket = ud.split_qs(ud.unquote(ticket))
            gatherer = self._hire_gatherer(ud.URL(ticket['referer'][0]))
            return gatherer.parse_file(target, ticket)
        # RSS_AGGRESSIVE = False
        gatherer = self._hire_gatherer(target)
        gatherer.isRSS = True
        item = gatherer.parse_item(target)
        if item['type'] in ['magnet', 'link']:
            return item['link']
        return gatherer.parse_file(ud.URL(item['link']), item['ticket'])

    def _order_page(self, target, query):
        # type: (urldealer.URL, werkzeug.datastructures.MultiDict) -> Iterable
        gatherer = self._hire_gatherer(target)
        return gatherer.get_page(gatherer.fetch(target))

    @tb.timeit
    def _get_data(self, order, target, query):
        # type: (Text, urldealer.URL, werkzeug.datastructures.MultiDict)
        # -> Union[str, fetchers.Response, Iterable]
        data = getattr(self, '_order_{}'.format(order))(target, query)
        log.info('Cumulative fetching size : %s', fetchers.fetcher.size_text(fetchers.fetcher.cum_size))
        return data

    def request(self, order, query):
        # type: (str, werkzeug.datastructures.MultiDict) -> Union[str, fetchers.Response, Iterable]
        if query.get('url'):
            target = ud.URL(ud.unquote(query['url']))
        elif query.get('site'):
            # list_by_alias(), rss_by_alias()
            class_ = self._find_gatherer(query.get('site'))
            target = ud.URL(class_.LIST_URL % query.get('board'))
        else:
            raise MyFlaskException('There is no target page.')
        # query handling...
        search_key = query.get('search')
        if search_key:
            target.update_qs('search={}'.format(search_key))
        page_num = query.get('page')
        if page_num > 0:
            target.update_qs('page={}'.format(page_num))
        log.info('%s mode', order.upper())
        return self._get_data(order, target, query)

