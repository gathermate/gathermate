# -*- coding: utf-8 -*-

import Cookie
import json
import logging as log
import httplib
import importlib

from apps.common.exceptions import MyFlaskException
from apps.common.cache import cache
from apps.common import urldealer as ud

fetcher = None

def hire_fetcher(config):
    global fetcher
    backend = config.get('BACKEND', '')
    if backend == 'GoogleAppEngine':
        fetcher = Urlfetch(config.get('FETCHER'),
                           importlib.import_module('google.appengine.api.urlfetch'))
    else:
        fetcher = Requests(config.get('FETCHER'),
                           importlib.import_module('requests'))
    return fetcher


class Response(object):
    '''
    This class is just to avoid cache error : PicklingError
    '''
    def __init__(self, headers, content, code, url, final_url):
        # type: (Dict[Text, Text], str, int, Text, Text) -> None
        self.headers = headers
        self.content = content
        self.status_code = code
        self.url = url
        self.final_url = final_url

class Fetcher(object):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    }
    UNITS = {
        'byte': 1.0,
        'KB': 1024.0,
        'MB': 1024.0 ** 2,
        'GB': 1024.0 ** 3,
    }
    COOKIE_ATTRS = ['expires', 'path', 'comment', 'domain', 'max-age', 'secure', 'version', 'httponly']
    THRESHOLD = 50
    cum_size = 0.0

    def __init__(self, config, module):
        # type : (Dict[Text, Union[Text, str, int]], Callable) -> None
        self.config = config
        self.module = module
        self.timeout = cache.FETCHER_TIMEOUT
        self.cookie_timeout = cache.FETCHER_COOKIE_TIMEOUT
        self.deadline = config.get('DEADLINE', 30)
        self.counter = 0
        self.current_response = None
        log.debug('Using {} module as current fetcher.'.format(type(self).__name__))

    def fetch(self, url, referer=None, method='GET', payload=None, forced_update=False, follow_redirects=False):
        # type: (urldealer.URL, str, str, Dict[Text, Text], bool) -> Response
        self.counter += 1
        if self.counter > self.THRESHOLD:
            log.error('Fetching counter exceeds threshold by a request. : %d', self.counter)
            raise MyFlaskException('Too many fetchings by a request.')
        key = cache.create_key(url.text, payload=payload)
        @cache.cached(timeout=self.timeout, key_prefix=key, forced_update=lambda:forced_update)
        def cached_fetch():
            # type: () -> Response
            log.debug('This fetching will update its cache.')
            log.debug('Fetching [...{0}{1}]'
                      .format(url.path, '?%s' % url.query if url.query else ''))
            r = None
            for _ in range(1):
                try:
                    r = self._fetch(url,
                                    deadline=self.deadline,
                                    payload=payload,
                                    method=method,
                                    headers=self._get_headers(url, referer),
                                    follow_redirects=follow_redirects)
                except httplib.BadStatusLine:
                    MyFlaskException.trace_error()
                except Exception as e:
                    MyFlaskException.trace_error()
                    if type(e) in self._get_retry_exceptions():
                        log.warning('Retry fetching...')
                        continue
                    raise MyFlaskException('%s,  while fetching [%s]', e.message, url.text)
                break
            r.key = key
            current_size = len(r.content)
            log.debug('Fetched {0:s} from [...{1}{2}]'
                      .format(self.size_text(current_size),
                              url.path,
                              '?%s' % url.query if url.query else ''))
            self.cum_size += current_size
            self._handle_response(url, r)
            return r
        return cached_fetch()

    def _get_headers(self, url, referer):
        # type: (urldealer.URL, Text) -> Dict[Text, Text]
        headers = {}
        for k, v in self.HEADERS.items():
            headers[k] = v
        headers['referer'] = referer if referer else ''
        cookie = self._get_cookie(url)
        if cookie:
            headers['cookie'] = cookie
        return headers

    def size_text(self, byte):
        #type: (int) -> Text
        unit = 'KB'
        size = byte / self.UNITS.get(unit)
        return u'{0:,.2f} {1:s}'.format(size, unit)

    def _handle_response(self, url, r):
        # type: (urldealer.URL, Response) -> None
        self.current_response = r
        status_code = str(r.status_code)
        if status_code[0] in ['4', '5']:
            raise MyFlaskException('''
                Destination URL not working.
                Content size: %d,
                Status Code: %d,
                Headers: %s''' % (len(r.content), r.status_code, r.headers), response=r)
        self.url = url.text
        set_cookie = r.headers.get('set-cookie')
        if set_cookie:
            self._set_cookie(url, set_cookie)

    def _get_cookie(self, url):
        # type: (urldealer.URL) -> Text
        cookie = cache.get(cache.create_key(url.hostname) + '-cookies')
        if cookie:
            return cookie
        return Cookie.SimpleCookie().output(self.COOKIE_ATTRS, header='', sep=';')

    def _set_cookie(self, url, new_cookie):
        # type: (urldealer.URL, str) -> None
        key = cache.create_key(url.hostname) + '-cookies'
        old_cookie = Cookie.SimpleCookie(str(cache.get(key)))
        old_cookie.load(new_cookie)
        cookie = old_cookie.output(self.COOKIE_ATTRS, header='', sep=';').strip()
        cache.set(key, cookie, timeout=self.cookie_timeout)

    def json_dump(self, _dict):
        # type: (Dict[object, object]) -> Text
        return json.dump(_dict)

    def _fetch(self, url, method='GET', payload=None, deadline=30, headers=None, follow_redirects=False):
        # type: (urldealer.URL, str, Dict[str, str], int, Dict[str, str], bool) -> Response
        raise NotImplementedError

    def _get_retry_exceptions(self):
        # type: () -> list[Exception]
        raise NotImplementedError

class Requests(Fetcher):

    # Override
    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # type: (urldealer.URL, int, str, Dict[Text, Text], Dict[Text, Text], bool) -> Response
        r = self.module.request(
            method.upper(),
            url.text,
            timeout=deadline,
            data=payload if method.upper() == 'POST' else None,
            params=payload if method.upper() == 'GET' else None,
            json=self.json_dump(payload) if method.upper() == 'JSON' and payload else None,
            headers=headers,
            allow_redirects=follow_redirects)
        return Response(r.headers, r.content, r.status_code, url.text, r.url)

    # Override
    def _get_retry_exceptions(self):
        # type: () -> list[Exception]
        return [self.module.exceptions.ConnectionError, self.module.exceptions.ChunkedEncodingError]

class Urlfetch(Fetcher):

    # Override
    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # type: (urldealer.URL, int, str, Dict[Text, Text], Dict[Text, Text], bool) -> Response
        if payload:
            payload = ud.unsplit_qs(payload)
        r = self.module.fetch(
            url.text,
            deadline=deadline,
            payload=payload,
            method='POST' if method.upper() == 'JSON' else method,
            headers=headers,
            follow_redirects=follow_redirects)
        r.url = r.final_url if r.final_url else url.text
        return Response(r.headers, r.content, r.status_code, url.text, r.url)

    # Override
    def _get_retry_exceptions(self):
        # type: () -> list[Exception]
        return [self.module.DNSLookupFailedError]
