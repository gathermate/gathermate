# -*- coding: utf-8 -*-

import logging

import packer
from apps.common import fetchers
from apps.common.exceptions import MyFlaskException
from apps.common import toolbox as tb
from apps.common import urldealer as ud
from apps.common.manager import Manager

log = logging.getLogger(__name__)

def hire_manager(config):
    # type: (flask.config.Config) -> ScrapmateManager
    packer.ACCEPTED_EXT = config.get('ACCEPTED_EXT', [])
    return ScrapmateManager(config)


class ScrapmateManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(ScrapmateManager, self).__init__(config)
        scrapers = self._register_modules('apps.scrapmate.boards', 'Scraper')
        self.__scraper_classes = {ud.Url(class_.URL).hostname: class_ for name, class_ in scrapers.iteritems()}

    def _hire_scraper(self, target):
        # type: (urldealer.Url) -> Type[scraper.Scraper]
        host = target.hostname if target.hostname else target.netloc
        if not host:
            raise MyFlaskException('Target URL is wrong : %s' % target.text)
        try:
            class_ = self.__scraper_classes[host]
        except KeyError:
            MyFlaskException.trace_error()
            class_ = self._find_scraper(host)
        log.debug("%s class matches with [%s].", class_.__name__, target.text)
        return self._train_scraper(class_, self.config.get('SCRAPERS'))

    def _find_scraper(self, alias):
        # type: (str) -> Type[scraper.Scraper]
        for host, class_ in self.__scraper_classes.iteritems():
            if alias in host:
                log.debug("%s class matches with [%s].", class_.__name__, alias)
                return class_
        raise MyFlaskException('There is no class associate with : {}'.format(alias))

    def _train_scraper(self, class_, config):
        # type: (Type[scraper.Scraper], Dict[str, Dict[str, Optional[bool, str, int, List[str]]]])
        # -> Type[scraper.Scraper]
        instance_config = self._get_default_config(class_.__name__, config)
        scraper = class_(instance_config, fetchers.hire_fetcher(config=self.config))
        return scraper

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
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> str
        scraper = self._hire_scraper(target)
        scraper.isRSS = True
        length = query.get('length', None, type=int)
        if length is not None:
            scraper.length = length
        listing = scraper.parse_list(target)
        return packer.pack_rss(scraper.parse_items(listing))

    def _order_item(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]])
        # -> List[Dict[str, Union[str, unicode]]]
        scraper = self._hire_scraper(target)
        items = scraper.parse_item(target)
        return packer.pack_item(items)

    def _order_list(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]])
        # -> Dict[str, Union[int, List[Tuple[int, Dict[str, Union[int, str, unicode]]]]]]
        scraper = self._hire_scraper(target)
        listing = scraper.parse_list(target)
        return packer.pack_list(listing)

    def _order_down(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> fetchers.Response
        ticket = query.get('ticket')
        if ticket:
            ticket = ud.split_qs(ud.unquote(ticket))
            scraper = self._hire_scraper(ud.Url(ticket['referer']))
            return scraper.parse_file(target, ticket)
        # RSS_AGGRESSIVE = False
        scraper = self._hire_scraper(target)
        scraper.isRSS = True
        items = scraper.parse_item(target)
        if len(items) is 0:
            raise MyFlaskException('No items found.')
        if items[0]['type'] in ['magnet', 'link']:
            return items[0]['link']
        return scraper.parse_file(ud.Url(items[0]['link']), items[0]['ticket'])

    def _order_page(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> Iterable
        scraper = self._hire_scraper(target)
        return scraper.get_page(scraper.fetch(target))

    @tb.timeit
    def _get_data(self, order, target, query):
        # type: (Text, urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]])
        # -> Union[str, fetchers.Response, Iterable]
        data = getattr(self, '_order_{}'.format(order))(target, query)
        return data

    def request(self, order, query):
        # type: (str, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> Union[str, fetchers.Response, Iterable]
        if query.get('url'):
            target = ud.Url(ud.unquote(query['url']))
        elif query.get('site'):
            # list_by_alias(), rss_by_alias()
            class_ = self._find_scraper(query.get('site'))
            target = ud.Url(class_.LIST_URL % query.get('board'))
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

