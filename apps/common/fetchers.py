# -*- coding: utf-8 -*-

import Cookie
import json
import logging
import httplib
import importlib

from apps.common.exceptions import MyFlaskException
from apps.common.cache import cache
from apps.common import urldealer as ud

log = logging.getLogger(__name__)

fetcher = None

def hire_fetcher(config=None):
    global fetcher
    if config is None:
        fetcher = Requests({},
                           importlib.import_module('requests'))
        return fetcher
    software = config.get('SOFTWARE', '')
    if software == 'GoogleAppEngine':
        fetcher = Urlfetch(config.get('FETCHER'),
                           importlib.import_module('google.appengine.api.urlfetch'))
    else:
        fetcher = Requests(config.get('FETCHER'),
                           importlib.import_module('requests'))
    return fetcher


class Response(object):

    def __init__(self, url, response):
        # type: (str, Union[requests.models.Response, google.appengine.api.urlfetch._URLFetchResult]) -> None
        self.url = url
        self.origin = response
        self.headers = response.headers
        self.content = response.content
        self.status_code = response.status_code
        self.final_url = response.url


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

    def fetch(self, url, referer=None, method='GET', payload=None, headers=None, forced_update=False, follow_redirects=False, cached=True):
        # type: (Union[urldealer.Url, str], str, str, Dict[str, str], Dict[str, str], boolean, boolean, boolean) -> Response
        url = ud.Url(url) if type(url) is not ud.Url else url
        self.counter += 1
        if self.counter > self.THRESHOLD:
            log.error('Fetching counter exceeds threshold by a request. : %d', self.counter)
            raise MyFlaskException('Too many fetchings by a request.')
        if cached:
            key = cache.create_key(ud.Url(url.text).update_query(payload).text if payload else url.text)
            cached_fetch = cache.cached(timeout=self.timeout, key_prefix=key, forced_update=lambda:forced_update)(self.cacheable_fetch)
            return cached_fetch(url, referer, method, payload, headers, follow_redirects, key)
        else:
            log.debug('This fetching will be not cached.')
            return self.cacheable_fetch(url, referer, method, payload, headers, follow_redirects)

    def cacheable_fetch(self, url, referer=None, method='GET', payload=None, headers=None, follow_redirects=False, key=None):
        # type: () -> Response
        log.debug('Fetching [%s://%s%s%s]',
                  url.scheme,
                  url.netloc,
                  url.path,
                  '...' if url.query else '')
        r = None
        for _ in range(2):
            try:
                r = self._fetch(url,
                                deadline=self.deadline,
                                payload=payload,
                                method=method,
                                headers=self._get_headers(url, referer, headers),
                                follow_redirects=follow_redirects)
            except httplib.BadStatusLine:
                MyFlaskException.trace_error()
            except Exception as e:
                MyFlaskException.trace_error()
                if type(e) in self._get_retry_exceptions():
                    log.warning('Retry fetching...')
                    continue
                raise MyFlaskException('%s, while fetching [%s]', e.message, url.text)
            break
        if not r:
            raise MyFlaskException('Failed to fetch [%s]', url.text)
        r.key = key
        current_size = len(r.content)
        log.debug('Fetched %s from [%s://%s%s%s]',
                  self.size_text(current_size),
                  url.scheme,
                  url.netloc,
                  url.path,
                  '...' if url.query else '')
        self.cum_size += current_size
        self._handle_response(url, r)
        return r

    def _get_headers(self, url, referer, headers):
        # type: (urldealer.Url, str, Dict[str, str]) -> Dict[str, str]
        new_headers = { k: v for k, v in self.HEADERS.iteritems() }
        new_headers['referer'] = referer if referer else ''
        if headers is not None:
            new_headers.update(headers)
            new_cookie = new_headers.pop('cookie', None)
            if new_cookie is not None:
                self.set_cookie(str(new_cookie), url)
        cookie = self.get_cookie(url, tostring=True)
        if cookie != '':
            new_headers['cookie'] = cookie
        return new_headers

    def size_text(self, byte):
        #type: (int) -> Text
        unit = 'KB'
        size = byte / self.UNITS.get(unit)
        return u'{0:,.2f} {1:s}'.format(size, unit)

    def _handle_response(self, url, r):
        # type: (urldealer.Url, Response) -> None
        self.current_response = r
        status_code = str(r.status_code)
        if status_code[0] in ['4', '5']:
            raise MyFlaskException('Destination URL not working.\n' +
                                   'Content size: %d,\n' % len(r.content) +
                                   'Status Code: %d,\n' % r.status_code +
                                   'Headers: %s,\n' % r.headers +
                                   'Content: \n%s\n' % r.content, response=r)
        self.url = url.text
        set_cookie = r.headers.get('set-cookie')
        if set_cookie:
            self.set_cookie(set_cookie, url)

    @classmethod
    def get_cookie(cls, url, tostring=False):
        # type: (Union[str, urldealer.Url]) -> str
        url = ud.Url(url) if type(url) is str else url
        cookie = ''
        try:
            cookie = cache.get(cache.create_key((url.domain if url.domain else url.hostname) + '-cookies'))
        except Exception as e:
            # http://116.122.159.146/
            log.warning(e.message)
        if tostring:
            return cookie if cookie else Cookie.SimpleCookie().output(cls.COOKIE_ATTRS, header='', sep=';')
        else:
            return Cookie.SimpleCookie(str(cookie)) if cookie else Cookie.SimpleCookie()

    @classmethod
    def set_cookie(cls, cookie, url):
        # type: (Union[str, urldealer.Url], Union[str, http.cookies.Morsel]) -> None
        if type(url) is not ud.Url:
            url = ud.Url(url)
        if type(cookie) is not Cookie.SimpleCookie:
            cookie = Cookie.SimpleCookie(str(cookie))
        try:
            key = cache.create_key((url.domain if url.domain else url.hostname) + '-cookies')
            cookies = Cookie.SimpleCookie(str(cache.get(key)))
            cookies.load(cookie)
            cookies = cookies.output(cls.COOKIE_ATTRS, header='', sep=';').strip()
            cache.set(key, cookies, timeout=0)
        except Exception as e:
            # http://116.122.159.146/
            log.warning(e.message)

    @staticmethod
    def reset_cookie(url):
        # type: (Union[str, urldealer.Url]) -> None
        url = ud.Url(url) if type(url) is str else url
        key = cache.create_key((url.domain if url.domain else url.hostname) + '-cookies')
        cache.delete(key)

    def _fetch(self, url, method='GET', payload=None, deadline=30, headers=None, follow_redirects=False):
        # type: (urldealer.Url, str, Dict[str, str], int, Dict[str, str], bool) -> Response
        raise NotImplementedError

    def _get_retry_exceptions(self):
        # type: () -> list[Exception]
        raise NotImplementedError

class Requests(Fetcher):

    # Override
    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # type: (urldealer.Url, int, str, Dict[str, str], Dict[str, str], bool) -> Response
        r = self.module.request(
            'POST' if method.upper() == 'JSON' else method.upper(),
            url.text,
            timeout=deadline,
            data=payload if method.upper() == 'POST' else None,
            params=payload if method.upper() == 'GET' else None,
            json=payload if method.upper() == 'JSON' else None,
            headers=headers,
            allow_redirects=follow_redirects)
        return Response(url.text, r)

    # Override
    def _get_retry_exceptions(self):
        # type: () -> list[Exception]
        return [self.module.exceptions.ConnectionError, self.module.exceptions.ChunkedEncodingError]

class Urlfetch(Fetcher):

    # Override
    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # type: (urldealer.Url, int, str, Dict[str, str], Dict[str, str], bool) -> Response
        if method.upper() == 'JSON':
            payload = json.dumps(payload)
            headers['Content-Type'] = 'application/json'
            method = 'POST'
        else:
            payload = ud.unsplit_qs(payload)
        r = self.module.fetch(
            url.text,
            deadline=deadline,
            payload=payload,
            method=method.upper(),
            headers=headers,
            follow_redirects=follow_redirects)
        r.url = r.final_url if r.final_url else url.text
        return Response(url.text, r)

    # Override
    def _get_retry_exceptions(self):
        # type: () -> list[Exception]
        return []
