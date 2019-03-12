# -*- coding: utf-8 -*-

import re
import logging
from functools import wraps

from lxml import etree
from concurrent import futures

from apps.common.exceptions import MyFlaskException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger(__name__)

class Scraper(object):
    def __init__(self, config, fetcher):
        # type: (Dict[str, object], Type[fetchers.Fetcher]) -> None
        self.encoding = config.get('ENCODING', 'utf-8')
        self.config = config
        self.fetcher = fetcher
        self.set_login(config)

    def set_login(self, config):
        # type: (Dict[str, object]) -> None
        self.login_info = {}

    ESCAPE_REGEXP = re.compile(r'\%..')
    def parse_file(self, url, ticket):
        # type: (urldealer.Url, Type[Dict[Text, Union[Text, List[Text]]]]) -> Response
        down_response = self.get_file(url, ticket)
        if not down_response or not down_response.headers.get('Content-Disposition'):
            log.error('HEADERS : %s', down_response.headers)
            raise MyFlaskException('Could not download : {}'.format(url.text),
                     response=self.fetcher.current_response)
        filename = tb.filename_from_headers(down_response.headers)
        if not self.ESCAPE_REGEXP.search(filename):
            filename = ud.quote(filename)
        down_response.filename = filename
        log.info('Downloading : [%s]', filename)
        down_response.headers['content-type'] = tb.get_mime(filename)
        return down_response

    def etree(self, response, encoding='utf-8'):
        # type: (Response, Text) -> lxml.etree._Element
        return etree.HTML(response.content.decode(encoding, 'replace'))

    def fetch_and_etree(self, url, referer=None, encoding='utf-8'):
        # type: (Union[Text, urldealer.Url], Text, Text) -> lxml.etree._Element
        return self.etree(self.fetch(url, referer=referer), encoding=encoding)

    def _log_result(self, url):
        # type: (urldealer.Url) -> None
        log.debug('Parsing [...%s%s] is done.',
                  url.path, '?%s' % url.query if url.query else '')

    def credential(self):
        # type: () -> None
        url = ud.Url(self.login_info.get('url'))
        self.fetcher.fetch(url,
                           referer=self.login_info.get('referer', self.URL),
                           method=self.login_info.get('method', 'POST').upper(),
                           payload=self.login_info.get('payload', None),
                           follow_redirects=self.login_info.get('follow_redirects', False),
                           forced_update=True)

    def check_login(self, r):
        # type: (Response) -> Optional(re.MatchObject, boolean)
        return self.login_info['denied'].search(r.content) or False

    def fetch(self, url, **kwargs):
        # type: (Union[urldealer.Url, Text], Optional[Dict[Text, object]]) -> Response
        url = ud.Url(url) if not type(url) is ud.Url else url
        r = self.fetcher.fetch(url, **kwargs)
        if self.login_info and self.check_login(r):
            log.debug('Login is required.')
            self.credential()
            log.debug('Refetching [%s]', url.text)
            r = self.fetcher.fetch(url, forced_update=True, **kwargs)
            if self.check_login(r):
                raise MyFlaskException('Could not login.',
                         response=self.fetcher.current_response)
        return r

    def safe_loop(self, elements, **kwargs):
        # type: (lxml.etree.Element, Optional[Dict[Text, object]]) -> Callable
        def handle_element(f):
            @wraps(f)
            def decorate():
                self.extract_info = {}
                for idx, element in enumerate(elements):
                    self.extract_info['idx'] = idx
                    try:
                        item = f(element)
                        if item:
                            yield item
                    except:
                        MyFlaskException.trace_error()
            return decorate
        return handle_element

    def get_page(self, response):
        # type: (Response) -> Iterable
        root = self.etree(response, encoding=self.encoding)
        return etree.tostring(root,
                              pretty_print=True,
                              encoding=self.encoding)

class EpgScraper(Scraper):
    pass

class BoardScraper(Scraper):
    def __init__(self, config, fetcher):
        super(BoardScraper, self).__init__(config, fetcher)
        self.length = int(config.get('RSS_LENGTH', 1))
        self.check_length_count = 0
        self.next_page = 2
        self.isRSS = False
        self.articles = {}
        try:
            self.want_regex = self._get_want_regex(self.config.get('RSS_WANT', []))
        except:
            MyFlaskException.trace_error()
            self.want_regex = self._get_want_regex([])

    def get_list(self, response):
        # type: (Response) -> Generator
        raise NotImplementedError

    def get_item(self, response):
        # type: (Response) -> Generator
        raise NotImplementedError

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, Union[Text, Dict[Text, Text]]]) -> Response
        raise NotImplementedError

    def handle_query(self, url):
        # type: (urldealer.Url) -> None
        page_num = url.query_dict.pop('page', None)
        search_key = url.query_dict.pop('search', None)
        if search_key:
            self.handle_search(url, search_key)
        if page_num:
            self.handle_page(url, page_num)

    def handle_search(self, url, keyword):
        # type: (urldealer.Url, Text) -> None
        url.update_qs(self.SEARCH_QUERY % keyword)

    def handle_page(self, url, num):
        # type: (urldealer.Url, Text) -> None
        url.update_qs(self.PAGE_QUERY % int(num))

    def get_id_num(self, text):
        # type: (Text) -> int
        result = self.ID_REGEXP.search(text)
        return int(result.group(1)) if result else -1

    def parse_list(self, url):
        # type: (urldealer.Url) -> Union[Dict[Text, Dict[Text, Text]], Dict[Text, Union[int, Dict[Text, object]]]]
        self.handle_query(url)
        response = self.fetch(url)
        current_ids = []
        try:
            # self.get_list() returns a generator that generates a dictionary.
            for article in self.get_list(response):
                id_num = article.get('id', -1)
                if id_num < 0:
                    log.warning('Skipped article id : [%s]', id_num)
                    continue
                current_ids.append(id_num)
                article['link'] = ud.join(url.text, article['link'])
                self.articles[id_num] = article
        except:
            MyFlaskException.trace_error()
        self._log_result(url)
        self._paginate(url, response.content)
        if self.max_page > self.current_page:
            self.next_page = self.current_page + 1
        self._check_length(url, self.articles, current_ids)
        if self.isRSS:
            return self.articles
        return {
            'articles': self.articles,
            'current_page': self.current_page,
            'max_page': self.max_page,
        }

    def _paginate(self, url, content):
        # type: (urldealer.Url, str) -> None
        PAGE_REGEXP = re.compile(re.sub('%d', '(\d{1,5})', self.PAGE_QUERY))
        match = PAGE_REGEXP.search(url.text)
        self.current_page = int(match.group(1)) if match else 1
        log.debug('Current page number is %d' % self.current_page)
        result = PAGE_REGEXP.findall(content)
        pages = set([int(x) for x in result])
        if len(pages) > 0:
            self.max_page = max(pages)
            log.debug('Maximum page number is %d' % self.max_page)
        else:
            self.max_page = 1
            log.debug('There are no page hints.')

    def _check_length(self, url, articles, current_ids):
        # type: (urldealer.Url, Dict[Text, Dict[Text, Text]], List[Text]) -> None
        total = len(articles)
        if total < 1:
            raise MyFlaskException('There are no articles that could be parsed : {}'.format(url.text),
                     response=self.fetcher.current_response)
        current = len(current_ids)
        if current < 1:
            log.warning('Current page is empty. : %s', url.text)
            return
        self.check_length_count += 1
        if self.check_length_count > 5:
            log.error('Too many loops...')
            return
        log.debug("Articles of current page : %d", current)
        if not self.isRSS:
            return
        if total > self.length:
            log.debug('Shorten articles from %s to %s', total, self.length)
            self._remove_list(articles, current_ids, total - self.length)
            log.debug("Total articles : %d", len(articles))
        elif total < self.length:
            log.debug('Extend articles from %s to %s', total, self.length)
            self._add_list(url)

    def _remove_list(self, articles, current_ids, target):
        # type: (Dict[Text, Dict[Text, Text]], List[Text], int) -> None
        current_ids.sort()
        del current_ids[target:]
        for key in current_ids:
            articles.pop(key, None)
        log.debug('%d articles were deleted.', len(current_ids))

    def _add_list(self, url):
        # type: (urldealer.Url) -> None
        if not self.max_page > self.next_page:
            log.debug('There is no more pages.')
            return
        self.handle_page(url, self.next_page)
        self.next_page += 1
        self.parse_list(url)

    def parse_items(self, articles):
        # type: (Dict[str, Dict[str, str]]) -> Iterable
        if not self.config.get('RSS_AGGRESSIVE'):
            return self._parse_item_from_list(articles)
        urls = [ud.Url(article['link']) for article in articles.values()]
        if self.config.get('RSS_ASYNC', False):
            with futures.ThreadPoolExecutor(max_workers=self.config.get('RSS_WORKERS', 1),
                                            thread_name_prefix="_get_item_async") as exe:
                return exe.map(self.parse_item, urls)
        else:
            result = []
            for url in urls:
                result.append(self.parse_item(url))
            return result

    def parse_item(self, article_url):
        # type: (Union[urldealer.Url, List[urldealer.Url]]) -> List[Optional[Dict[str, str]]]
        items = []
        try:
            r = self.fetch(article_url)
            # self.get_item() returns a generator that generates a dictionary.
            for item in self.get_item(r):
                items.append(item)
                if not item.get('ticket'):
                    item['ticket'] = {}
                item['ticket']['referer'] = article_url.text
                log.debug('[%s] @ [%s]', item['name'], item['link'])
                if item['type'] == 'file' and not ud.Url(item['link']).netloc:
                    item['link'] = unicode(ud.join(article_url.text, item['link']))
        except:
            MyFlaskException.trace_error()
        self._log_result(article_url)
        if len(items) is not 0:
            if self.isRSS and not self.config.get('RSS_AGGRESSIVE'):
                return [self._want(items)]
        else:
            log.error('No items found : %s', article_url)
        return items

    def _want(self, items):
        # type: (List[Dict[str, str]]) -> Optional[Dict[str, str]]
        for want in self.want_regex:
            for item in items:
                match = want.search(item['name'].lower())
                if match:
                    log.debug('[%s] matched.', match.group(0))
                    return item
        return items[0]

    def _get_want_regex(self, want_list):
        # type: (List[str]) -> List[_sre.SRE_Pattern]
        if not want_list:
            return [re.compile(r'\.torrent$')]
        return [re.compile(keyword, re.I) for keyword in want_list]


    def _parse_item_from_list(self, articles):
        new_articles = []
        for id_num, article in articles.iteritems():
            item = {}
            item['name'] = article['title']
            item['link'] = article['link']
            item['type'] = 'unknown'
            new_articles.append([item])
        return new_articles
