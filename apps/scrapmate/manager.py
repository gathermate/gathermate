# -*- coding: utf-8 -*-

import logging

import packer
from apps.common import fetchers
from apps.common.exceptions import MyFlaskException
from apps.common import toolbox as tb
from apps.common import urldealer as ud
from apps.common.manager import Manager
from apps.scrapmate.scraper import BoardScraper

log = logging.getLogger(__name__)

def hire_manager(config):
    # type: (flask.config.Config) -> ScrapmateManager
    packer.ACCEPTED_EXT = config['ACCEPTED_EXT']
    return ScrapmateManager(config)


class ScrapmateManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(ScrapmateManager, self).__init__(config)
        scrapers = self._register_modules('apps.scrapmate.boards', 'Scraper')
        self.__scraper_classes = {ud.Url(class_.URL).domain: class_ for name, class_ in scrapers.iteritems()}

    def _hire_board(self, target):
        # type: (urldealer.Url) -> Type[scraper.Scraper]
        domain = target.domain if target.domain else target.hostname
        if not domain:
            raise MyFlaskException('Target URL is wrong : %s' % target.text)
        try:
            class_ = self.__scraper_classes[domain]
        except KeyError:
            MyFlaskException.trace_error()
            class_ = self._find_scraper(domain)
        log.debug("%s class matches with [%s].", class_.__name__, target.text)
        return self._train_baord(class_, self.config.get('SCRAPERS'))

    def _find_scraper(self, alias):
        # type: (str) -> Type[scraper.Scraper]
        for domain, class_ in self.__scraper_classes.iteritems():
            if alias in domain:
                log.debug("%s class matches with [%s].", class_.__name__, alias)
                return class_
        raise MyFlaskException('There is no class associate with : {}'.format(alias))

    def _train_baord(self, class_, config):
        # type: (Type[scraper.Scraper], Dict[str, Dict[str, Optional[bool, str, int, List[str]]]])
        # -> Type[scraper.Scraper]
        default_config = {
            'ENCODING': 'utf-8',
            'RSS_WANT': self.config.get('RSS_WANT', []),
            'RSS_AGGRESSIVE': self.config.get('RSS_AGGRESSIVE', False),
            'RSS_ASYNC': self.config.get('RSS_ASYNC', False),
            'RSS_WORKERS': self.config.get('RSS_WORKERS', 1),
            'RSS_LENGTH': self.config.get('RSS_LENGTH', 5),
            'LOGIN_INFO': self.config.get('LOGIN_INFO')
        }
        if config.get(class_.__name__, None):
            default_config.update(config.get(class_.__name__))
        return class_(fetchers.hire_fetcher(self.config['FETCHER']),
                      default_config['ENCODING'],
                      default_config['LOGIN_INFO'],
                      default_config['RSS_LENGTH'],
                      default_config['RSS_WANT'],
                      default_config['RSS_AGGRESSIVE'],
                      default_config['RSS_ASYNC'],
                      default_config['RSS_WORKERS'])

    def _order_rss(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> str
        board = self._hire_board(target)
        board.isRSS = True
        length = query.get('length', None, type=int)
        if length is not None:
            board.length = length
        listing = board.parse_list(target)
        return packer.pack_rss(board.parse_items(listing))

    def _order_item(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]])
        # -> List[Dict[str, Union[str, unicode]]]
        board = self._hire_board(target)
        items = board.parse_item(target)
        return packer.pack_item(items)

    def _order_list(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]])
        # -> Dict[str, Union[int, List[Tuple[int, Dict[str, Union[int, str, unicode]]]]]]
        board = self._hire_board(target)
        listing = board.parse_list(target)
        return packer.pack_list(listing)

    def _order_down(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> fetchers.Response
        ticket = query.get('ticket')
        if ticket:
            ticket = ud.split_qs(ud.unquote(ticket))
            board = self._hire_board(ud.Url(ticket['referer']))
            return board.parse_file(target, ticket)
        # RSS_AGGRESSIVE = False
        board = self._hire_board(target)
        board.isRSS = True
        items = board.parse_item(target)
        if len(items) is 0:
            raise MyFlaskException('No items found.')
        if items[0]['type'] in ['magnet', 'link']:
            return items[0]['link']
        return board.parse_file(ud.Url(items[0]['link']), items[0]['ticket'])

    def _order_page(self, target, query):
        # type: (urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]]) -> Iterable
        board = self._hire_board(target)
        return board.get_page(board.fetch(target))

    @tb.timeit
    def _get_data(self, order, target, query):
        # type: (Text, urldealer.Url, apps.common.datastructures.MultiDict[unicode, List[unicode]])
        # -> Union[str, fetchers.Response, Iterable]
        data = getattr(self, '_order_{}'.format(order))(target, query)
        return data

    def request_board(self, order, query):
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
        log.debug('%s mode', order.upper())
        return self._get_data(order, target, query)