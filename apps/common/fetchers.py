# -*- coding: utf-8 -*-

import Cookie
import json
import logging
import httplib
import importlib
import os

from apps.common.exceptions import MyFlaskException
from apps.common import caching
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger(__name__)

def hire_fetcher(config=None):
    software = config.get('SOFTWARE', '')
    if config.get('FETCHER', None) is not None:
        config = config.get('FETCHER')
    deadline = config.get('DEADLINE')
    cache_timeout = config.get('CACHE_TIMEOUT')
    cookie_timeout = config.get('COOKIE_TIMEOUT')
    cookie_path = config.get('COOKIE_PATH')

    if software == 'GoogleAppEngine':
        fetcher = Urlfetch(importlib.import_module('google.appengine.api.urlfetch'),
                           deadline, cache_timeout, cookie_timeout, cookie_path)
    else:
        fetcher = Requests(importlib.import_module('requests'),
                           deadline, cache_timeout, cookie_timeout, cookie_path)
    return fetcher


class Response(object):

    def __init__(self, url, response):
        # type: (str, Union[requests.models.Response, google.appengine.api.urlfetch._URLFetchResult]) -> None
        self.url = url
        self.headers = response.headers
        self.content = response.content
        self.status_code = response.status_code
        self.final_url = response.url


class Fetcher(object):
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
    }
    COOKIE_ATTRS = ['expires', 'path', 'comment', 'domain', 'max-age', 'secure', 'version', 'httponly']
    THRESHOLD = 50

    def __init__(self, module, deadline=30, cache_timeout=60,
                 cookie_timeout=0, cookie_path=None):
        # type : (Callable, int, int, int, Optional[str]) -> None
        self.module = module
        self.counter = 0
        self.current_response = None
        self.timeout = cache_timeout
        self.cookie_timeout = cookie_timeout
        self.deadline = deadline
        self.cookie_path = cookie_path

    def fetch(self, url, payload=None, forced_update=False, cached=True, **kwargs):
        # type: (Union[urldealer.Url, str], str, str, Dict[str, str], Dict[str, str], boolean, boolean, boolean) -> Response
        url = ud.Url(url) if type(url) is not ud.Url else url
        self.counter += 1
        if self.counter > self.THRESHOLD:
            log.error('Fetching counter exceeds threshold by a request. : %d', self.counter)
            raise MyFlaskException('Too many fetchings by a request.')
        if cached:
            key = caching.create_key(ud.Url(url.text).update_query(payload).text if payload else url.text)
            func = caching.cache.cached(timeout=self.timeout,
                                        key_prefix=key,
                                        forced_update=lambda:forced_update)(self.cacheable_fetch)
        else:
            key = None
            func = self.cacheable_fetch
        return func(url, payload=payload, key=key, **kwargs)

    def cacheable_fetch(self, url, referer=None, headers=None, key=None, **kwargs):
        # type: () -> Response
        r = None
        for _ in range(2):
            try:
                r = self._fetch(url,
                                deadline=self.deadline,
                                headers=self._get_headers(url, referer, headers),
                                **kwargs)
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
        log.debug('Fetched %s', tb.size_text(len(r.content)))
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
                self.set_cookie(str(new_cookie),
                                url,
                                path=self.cookie_path)
        cookie = self.get_cookie(url,
                                 tostring=True,
                                 path=self.cookie_path)
        if cookie != '':
            new_headers['cookie'] = cookie
        return new_headers

    def _handle_response(self, url, r):
        # type: (urldealer.Url, Response) -> None
        self.current_response = r
        self.url = url.text
        status_code = str(r.status_code)
        if status_code[0] in ['4', '5']:
            raise MyFlaskException('Destination URL not working.\n' +
                                   'URL: %s,\n' % url.text +
                                   'Content size: %d,\n' % len(r.content) +
                                   'Status Code: %d,\n' % r.status_code +
                                   'Headers: %s,\n' % r.headers +
                                   'Content: \n%s\n' % r.content, response=r)
        set_cookie = r.headers.get('set-cookie')
        if set_cookie:
            self.set_cookie(set_cookie, url,
                            path=self.cookie_path)

    @staticmethod
    def get_cookie_key(url):
        return caching.create_key((url.domain if url.domain else url.hostname) + '-cookies')

    @staticmethod
    def get_cookie_file(url, path):
        return os.path.join(path, '%s.txt' % (url.domain if url.domain else url.hostname))

    @classmethod
    def get_cookie(cls, url, tostring=False, path=None):
        # type: (Union[str, urldealer.Url]) -> str
        url = ud.Url(url) if type(url) is str else url
        cookie = ''
        try:
            if path is not None and os.path.exists(path):
                file = cls.get_cookie_file(url, path)
                if os.path.exists(file):
                    with open(file, 'r') as f:
                        cookie = f.read()
            else:
                cookie = caching.cache.get(cls.get_cookie_key(url))
        except Exception as e:
            # http://116.122.159.146/
            log.warning('%s : %s', e, e.message)
        if tostring:
            return cookie
        else:
            return Cookie.SimpleCookie(str(cookie))

    @classmethod
    def set_cookie(cls, cookie, url, path=None):
        # type: (Union[str, urldealer.Url], Union[str, http.cookies.Morsel]) -> None
        if type(url) is not ud.Url:
            url = ud.Url(url)
        if type(cookie) is not Cookie.SimpleCookie:
            cookie = Cookie.SimpleCookie(str(cookie))
        try:
            cookies = cls.get_cookie(url, path=path)
            cookies.load(cookie)
            cookies = cookies.output(cls.COOKIE_ATTRS, header='', sep=';').strip()
            if path is not None:
                if not os.path.exists(path):
                    os.makedirs(path)
                    log.debug('##### make path')
                with open(cls.get_cookie_file(url, path), 'w+' ) as f:
                    f.write(cookies)
            else:
                caching.cache.set(cls.get_cookie_key(url), cookies, timeout=0)
        except Exception as e:
            # http://116.122.159.146/
            log.warning(e.message)
            raise e

    @classmethod
    def reset_cookie(cls, url, path=None):
        # type: (Union[str, urldealer.Url]) -> None
        url = ud.Url(url) if type(url) is str else url
        if path is not None:
            os.remove(cls.get_cookie_file(url, path))
        else:
            key = Fetcher.get_cookie_key(url)
            caching.cache.delete(key)

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
