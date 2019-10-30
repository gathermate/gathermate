# -*- coding: utf-8 -*-

import logging

import packer
from apps.common.exceptions import GathermateException
from apps.common import toolbox as tb
from apps.common import urldealer as ud
from apps.common.manager import Manager

log = logging.getLogger()

def hire_manager(config):
    packer.ACCEPTED_EXT = config['ACCEPTED_EXT']
    return ScrapmateManager(config)


class ScrapmateManager(Manager):

    def __init__(self, config):
        super(ScrapmateManager, self).__init__(config)
        scrapers = self._register_modules('apps.scrapmate.boards', 'Scraper')
        self.__scraper_classes = {ud.Url(class_.URL).domain: class_ for name, class_ in scrapers.iteritems()}

    def _hire_board(self, target):
        domain = target.domain if target.domain else target.hostname
        if not domain:
            raise GathermateException('Target URL is wrong : %s' % target.text)
        try:
            class_ = self.__scraper_classes[domain]
        except KeyError:
            GathermateException.trace_error()
            class_ = self._find_scraper(domain)
        log.debug("%s class matches with [%s].", class_.__name__, target.text)
        return self._train_baord(class_, self.config.get('SCRAPERS'))

    def _find_scraper(self, alias):
        for domain, class_ in self.__scraper_classes.iteritems():
            if alias in domain:
                log.debug("%s class matches with [%s].", class_.__name__, alias)
                return class_
        raise GathermateException('There is no class associate with : {}'.format(alias))

    def _train_baord(self, class_, config):
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
        return class_(self._hire_fetcher(),
                      default_config['ENCODING'],
                      default_config['LOGIN_INFO'],
                      default_config['RSS_LENGTH'],
                      default_config['RSS_WANT'],
                      default_config['RSS_AGGRESSIVE'],
                      default_config['RSS_ASYNC'],
                      default_config['RSS_WORKERS'])

    def _order_rss(self, target, query):
        board = self._hire_board(target)
        board.isRSS = True
        length = query.get('length', None, type=int)
        if length is not None:
            board.length = length
        listing = board.parse_list(target)
        return packer.pack_rss(board.parse_items(listing))

    def _order_item(self, target, query):
        board = self._hire_board(target)
        items = board.parse_item(target)
        return packer.pack_item(items)

    def _order_list(self, target, query):
        board = self._hire_board(target)
        listing = board.parse_list(target)
        return packer.pack_list(listing)

    def _order_down(self, target, query):
        ticket = query.get('ticket')
        if ticket:
            ticket = ud.split_qs(ud.unquote(ticket))
            board = self._hire_board(ud.Url(ticket['referer']))
            return board.parse_file(target, ticket)
        # 'RSS_AGGRESSIVE = False' is doesn't have ticket
        board = self._hire_board(target)
        board.isRSS = True
        items = board.parse_item(target)
        if len(items) is 0:
            raise GathermateException('No items found.')
        if items[0]['type'] in ['magnet', 'link']:
            return items[0]['link']
        return board.parse_file(ud.Url(items[0]['link']), items[0]['ticket'])

    def _order_page(self, target, query):
        board = self._hire_board(target)
        return board.get_page(board.fetch(target))

    def _order_custom(self, target, query):
        board = self._hire_board(target)
        return board.get_custom(query)

    @tb.timeit
    def _get_data(self, order, target, query):
        data = getattr(self, '_order_{}'.format(order))(target, query)
        return data

    def request_board(self, order, query):
        if query.get('url'):
            target = ud.Url(ud.unquote(query['url']))
        elif query.get('site'):
            # list_by_alias(), rss_by_alias()
            class_ = self._find_scraper(query.get('site'))
            target = ud.Url(class_.LIST_URL % query.get('board'))
        else:
            raise GathermateException('There is no target page.')
        search_key = query.get('search')
        if search_key:
            target.update_qs('search={}'.format(search_key))
        page_num = query.get('page')
        if page_num > 0:
            target.update_qs('page={}'.format(page_num))
        log.debug('%s mode', order.upper())
        return self._get_data(order, target, query)
