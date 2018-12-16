# -*- coding: utf-8 -*-

import re
import logging as log
import traceback
from functools import wraps

from lxml import etree
import concurrent.futures as futures

from util import urldealer as ud
from util import toolbox as tb

class Gatherer(object):
    def __init__(self, config, fetcher):
        # type: (Dict[str, object], Type[fetchers.Fetcher]) -> None
        self.encoding = config.get('ENCODING', 'utf-8')
        self.length = int(config.get('RSS_LENGTH', 1))
        self.config = config
        self.fetcher = fetcher
        self.check_length_count = 0
        self.next_page = 2
        self.set_login(config)
        self.isRSS = False
        self.articles = {}
        self.want_regex = self._get_want_regex(self.config.get('RSS_WANT'))

    def handle_query(self, url):
        # type: (urldealer.URL) -> None
        page_num = url.query_dict.pop('page', None)
        search_key = url.query_dict.pop('search', None)
        if search_key:
            self.handle_search(url, search_key)
        if page_num:
            self.handle_page(url, page_num)

    def set_login(self, config):
        # type: (Dict[str, object]) -> None
        # Override if it is necessary.
        self.login_info = {}

    def handle_search(self, url, keyword):
        # type: (urldealer.URL, Text) -> None
        # Override if it is necessary.
        url.update_qs(self.SEARCH_QUERY % keyword)

    def handle_page(self, url, num):
        # type: (urldealer.URL, Text) -> None
        # Override if it is necessary.
        url.update_qs(self.PAGE_QUERY % int(num))

    def parse_list(self, url):
        # type: (urldealer.URL) -> Union[Dict[Text, Dict[Text, Text]], Dict[Text, Union[int, Dict[Text, object]]]]
        self.handle_query(url)
        response = self.fetch(url)
        current_ids = []

        try:
            # self.get_list() returns dictionary generator.
            for article in self.get_list(response):
                id_num = article.get('id')
                if id_num < 0:
                    log.warning('Skipped article id : [%s]', id_num)
                    continue
                current_ids.append(id_num)
                article['link'] = ud.join(url.text, article['link'])
                self.articles[id_num] = article
        except:
            self.trace_error()

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
        # type: (urldealer.URL, str) -> None
        #https://torrentwal.net/torrent_variety/torrent5.htm
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
        # type: (urldealer.URL, Dict[Text, Dict[Text, Text]], List[Text]) -> None
        total = len(articles)
        if total < 1:
            raise Exception('There are no articles that could be parsed : {}'.format(url.text))

        current = len(current_ids)

        self.check_length_count += 1
        if self.check_length_count > 5:
            log.error('Too many loops...')
            return

        if current < 1:
            log.warning('Current page is empty. : %s', url.text)
            return

        log.debug("Articles of current page : %d", current)

        if not self.isRSS:
            return

        if total > self.length:
            log.debug(
                'Shorten articles from %s to %s', total, self.length)
            self._remove_list(articles, current_ids, total - self.length)
            log.debug("Total articles : %d", len(articles))
        elif total < self.length:
            log.debug(
                'Extend articles from %s to %s', total, self.length)
            self._add_list(url)

    def _remove_list(self, articles, current_ids, target):
        # type: (Dict[Text, Dict[Text, Text]], List[Text], int) -> None
        current_ids.sort()
        del current_ids[target:]
        for key in current_ids:
            articles.pop(key, None)
        log.debug('%d articles were deleted.', len(current_ids))

    def _add_list(self, url):
        # type: (urldealer.URL) -> None
        if not self.max_page > self.next_page:
            log.debug('There is no more pages.')
            return
        self.handle_page(url, self.next_page)
        self.next_page += 1
        self.parse_list(url)

    def parse_items(self, articles):
        # type: (Dict[Text, Dict[Text, Text]]) -> Iterable
        if not self.config.get('RSS_AGGRESSIVE'):
            return self._parse_item_from_list(articles)

        urls = [ud.URL(article['link']) for article in articles.values()]
        if self.config.get('RSS_ASYNC', False):
            with futures.ThreadPoolExecutor(max_workers=self.config.get('RSS_WORKERS', 1),
                                            thread_name_prefix="_get_item_async") as exe:
                return exe.map(self.parse_item, urls)
        else:
            result = []
            for url in urls:
                result.append(self.parse_item(url))
            return result

    def _parse_item_from_list(self, articles):
        new_articles = []
        for id_num, article in articles.items():
            item = {}
            item['name'] = article['title']
            item['link'] = article['link']
            item['type'] = 'unknown'
            new_articles.append([item])

        return new_articles

    def parse_item(self, article_url):
        # type: (Union[urldealer.URL, List[urldealer.URL]]) -> List[Dict[Text, Text]]
        items = []
        try:
            r = self.fetch(article_url)
            # self.get_item() returns dictionary generator.
            for item in self.get_item(r):
                items.append(item)
                if not item.get('ticket'):
                    item['ticket'] = {}
                item['ticket']['referer'] = article_url.text
                log.debug('[%s] @ [%s]', item['name'], item['link'])
                if item['type'] == 'file' and not ud.URL(item['link']).netloc:
                    item['link'] = unicode(ud.join(article_url.text, item['link']))
        except:
            self.trace_error()

        self._log_result(article_url)

        if len(items) == 0:
            log.warning('No items found : %s', article_url)
            return items

        if self.isRSS and not self.config.get('RSS_AGGRESSIVE'):
            items = self._want(items)

        return items

    def _want(self, items):
        # type: (List[Dict[Text, Text]]) -> Dict[Text, Text]
        for want in self.want_regex:
            for item in items:
                match = want.search(item['name'])
                if match:
                    log.debug('[%s] matched.', match.group(0))
                    return item
        return items[0]

    def _get_want_regex(self, want_list):
        # type: (List[Text]) -> List[_sre.SRE_Pattern]
        if not want_list:
            return [re.compile(r'\.torrent$')]
        return [re.compile(keyword) for keyword in want_list]

    ESCAPE_REGEXP = re.compile(r'\%..')
    def parse_file(self, url, ticket):
        # type: (urldealer.URL, Dict[Text, Union[Text, Dict[Text, Text]]]) -> Response

        down_response = self.get_file(url, ticket)

        if not down_response or not down_response.headers.get('Content-Disposition'):
            log.error('HEADERS : %s', down_response.headers)
            raise Exception('Could not download : {}', url.text)

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
        # type: (Union[Text, urldealer.URL], Text, Text) -> lxml.etree._Element
        return self.etree(self.fetch(url, referer=referer), encoding=encoding)

    def get_id_num(self, text):
        # type: (Text) -> int
        result = self.ID_REGEXP.search(text)
        return int(result.group(1)) if result else -1

    magnet_regexp = re.compile(r'^magnet:\?xt=urn:btih:.*')
    def is_magnet(self, link):
        # type: (Text) -> Text
        return 'magnet' if self.magnet_regexp.search(link) else 'file'

    def _log_result(self, url):
        # type: (urldealer.URL) -> None
        log.debug('Parsing [...%s%s] is done.',
                  url.path, '?%s' % url.query if url.query else '')

    def _credential(self):
        # type: () -> None
        # Override if it is necessary.
        payload = self.login_info.get('fields')
        url = ud.URL(self.login_info.get('url'))
        referer = '{}://{}'.format(url.scheme, url.netloc)
        r = self.fetcher.fetch(url, referer=referer, method='POST', payload=payload, forced_update=True)

        regexp = re.compile(self.login_info.get('done'))
        if regexp.search(r.content):
            log.info('Login succeeded on {}://{}'.format(url.scheme, url.netloc))
        else:
            raise Exception('Could not login to [{}]'.format(url.netloc))

    def fetch(self, url, **kwargs):
        # type: (Union[urldealer.URL, Text], Optional[Dict[Text, object]]) -> Response
        url = ud.URL(url) if not type(url) is ud.URL else url
        r = self.fetcher.fetch(url, **kwargs)

        if self.login_info:
            denied = re.compile(self.login_info.get('denied'))
            if denied.search(r.content):
                log.info('Login required with {}://{}'.format(url.scheme, url.netloc))
                self._credential()
                log.debug('Refetching [{}]'.format(url.text))
                r = self.fetcher.fetch(url, forced_update=True, **kwargs)

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
                        self.trace_error()
            return decorate
        return handle_element

    def trace_error(self):
        # type: () -> None
        log.error('\n{}'.format(traceback.format_exc()))

    def get_list(self, response):
        # type: (Response) -> Generator
        # Override is required.
        raise NotImplementedError

    def get_item(self, response):
        # type: (Response) -> Generator
        # Override is required.
        raise NotImplementedError

    def get_file(self, url, ticket):
        # type: (urldealer.URL, Dict[Text, Union[Text, Dict[Text, Text]]]) -> Response
        # Override is required.
        raise NotImplementedError

    def get_page(self, response):
        # type: (Response) -> Iterable
        # Override it.
        root = self.etree(response, encoding=self.encoding)
        return etree.tostring(root,
                              pretty_print=True,
                              encoding=self.encoding)
