# -*- coding: utf-8 -*-

import re
import logging
from functools import wraps

from lxml import etree
from concurrent import futures

from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger()

class Scraper(object):
    def __init__(self, fetcher, encoding='utf-8', login_info=None):
        self.encoding = encoding
        self.fetcher = fetcher
        self.set_login(login_info)

    def set_login(self, login_info):
        self.login_info = {}

    ESCAPE_REGEXP = re.compile(r'\%..')
    def parse_file(self, url, ticket):
        down_response = self.get_file(url, ticket)
        if not down_response or not down_response.headers.get('Content-Disposition'):
            log.error('HEADERS : %s', down_response.headers)
            raise GathermateException('Could not download : {}'.format(url.text),
                     response=self.fetcher.current_response)
        filename = tb.filename_from_headers(down_response.headers)
        if not self.ESCAPE_REGEXP.search(filename):
            filename = ud.quote(filename)
        down_response.filename = filename
        log.info('Downloading : [%s]', filename)
        down_response.headers['content-type'] = tb.get_mime(filename)
        return down_response

    def etree(self, response, encoding='utf-8'):
        return etree.HTML(response.content.decode(encoding, 'replace'))

    def fetch_and_etree(self, url, referer=None, encoding='utf-8'):
        return self.etree(self.fetch(url, referer=referer), encoding=encoding)

    def _log_result(self, url):
        log.debug('Parsing [%s%s] is done.',
                  '...' + url.path if url.path else url.text, '?%s' % url.query if url.query else '')

    def credential(self):
        url = ud.Url(self.login_info.get('url'))
        self.fetcher.fetch(url,
                           referer=self.login_info.get('referer', self.URL),
                           method=self.login_info.get('method', 'POST').upper(),
                           payload=self.login_info.get('payload', None),
                           follow_redirects=self.login_info.get('follow_redirects', False),
                           forced_update=True)

    def check_login(self, r):
        return self.login_info['denied'].search(r.content) or False

    def fetch(self, url, **kwargs):
        url = ud.Url(url) if not type(url) is ud.Url else url
        r = self.fetcher.fetch(url, **kwargs)
        if self.login_info and self.check_login(r):
            log.debug('Login is required.')
            self.credential()
            log.debug('Refetching [%s]', url.text)
            r = self.fetcher.fetch(url, forced_update=True, **kwargs)
            if self.check_login(r):
                raise GathermateException('Could not login.',
                         response=self.fetcher.current_response)
        return r

    def safe_loop(self, elements, **kwargs):
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
                        GathermateException.trace_error()
            return decorate
        return handle_element

    def get_page(self, response):
        root = self.etree(response, encoding=self.encoding)
        return etree.tostring(root,
                              pretty_print=True,
                              encoding=self.encoding)


class BoardScraper(Scraper):
    def __init__(self,
                 fetcher,
                 encoding='utf-8',
                 login_info={},
                 rss_length=1,
                 rss_want=[],
                 rss_aggressive=False,
                 rss_async=False,
                 rss_workers=1):
        Scraper.__init__(self, fetcher, encoding, login_info)
        self.length = int(rss_length)
        self.want = rss_want
        self.aggressive = rss_aggressive
        self.async = rss_async
        self.workers = rss_workers
        self.check_length_count = 0
        self.next_page = 2
        self.isRSS = False
        self.articles = {}
        try:
            self.want_regex = self._get_want_regex(self.want)
        except:
            GathermateException.trace_error()
            self.want_regex = self._get_want_regex([])

    def get_list(self, response):
        raise NotImplementedError

    def get_item(self, response):
        raise NotImplementedError

    def get_file(self, url, ticket):
        raise NotImplementedError

    def handle_query(self, url):
        page_num = url.query_dict.pop('page', None)
        search_key = url.query_dict.pop('search', None)
        if search_key:
            self.handle_search(url, search_key)
        if page_num:
            self.handle_page(url, page_num)

    def handle_search(self, url, keyword):
        url.update_qs(self.SEARCH_QUERY % keyword)

    def handle_page(self, url, num):
        url.update_qs(self.PAGE_QUERY % int(num))

    def get_id_num(self, text):
        result = self.ID_REGEXP.search(text)
        return int(result.group(1)) if result else -1

    def parse_list(self, url):
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
            GathermateException.trace_error()
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
        total = len(articles)
        if total < 1:
            raise GathermateException('There are no articles that could be parsed : {}'.format(url.text),
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
        current_ids.sort()
        del current_ids[target:]
        for key in current_ids:
            articles.pop(key, None)
        log.debug('%d articles were deleted.', len(current_ids))

    def _add_list(self, url):
        if not self.max_page > self.next_page:
            log.debug('There is no more pages.')
            return
        self.handle_page(url, self.next_page)
        self.next_page += 1
        self.parse_list(url)

    def parse_items(self, articles):
        if not self.aggressive:
            for id_num, article in articles.iteritems():
                item = {}
                item['name'] = article['title']
                item['link'] = article['link']
                item['type'] = 'unknown'
                yield [item]
        else:
            urls = [ud.Url(article['link']) for article in articles.values()]
            if self.async:
                with futures.ThreadPoolExecutor(max_workers=self.workers,
                                                thread_name_prefix="_get_item_async") as exe:
                    fs = [exe.submit(self.parse_item, url) for url in urls]
                    for f in futures.as_completed(fs):
                        yield f.result()
            else:
                for url in urls:
                    yield self.parse_item(url)

    def parse_item(self, article_url):
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
                if item['type'] == 'file':
                    item_url = ud.Url(item['link'])
                    if not item_url.hostname or item_url.scheme:
                        item['link'] = unicode(ud.join(self.URL, item['link']))
        except:
            GathermateException.trace_error()
        self._log_result(article_url)
        if len(items) is not 0:
            if self.isRSS and not self.aggressive:
                return [self._want(items)]
        else:
            log.error('No items found : %s', article_url)
        return items

    def _want(self, items):
        torrent_list = []
        etc_list = []
        for item in items:
            if item['name'].endswith('.torrent'):
                torrent_list.append(item)
            else:
                etc_list.append(item)
        wanted = self.find_want(torrent_list)
        '''
        if wanted is None:
            wanted = self.find_want(etc_list)
        return wanted or (torrent_list or etc_list)[0]
        '''
        # It should return a torrent file in RSS.
        if not wanted and not torrent_list:
            return items[0]
        return wanted or torrent_list[0]


    def find_want(self, list_):
        for want in self.want_regex:
            for item in list_:
                match = want.search(item['name'].lower())
                if match:
                    log.debug('[%s] matched.', match.group(0))
                    return item
        return None

    def _get_want_regex(self, want_list):
        if not want_list:
            return [re.compile(r'\.torrent$')]
        return [re.compile(keyword, re.I) for keyword in want_list]
