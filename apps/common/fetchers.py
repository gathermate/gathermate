# -*- coding: utf-8 -*-

import Cookie
import json
import logging
import httplib
import importlib
import os

from apps.common.exceptions import GathermateException
from apps.common import caching
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger(__name__)

backend = os.environ.get('SERVER_SOFTWARE', '')
if backend.startswith('Google App Engine/') or backend.startswith('Development/'):
    urlfetch_errors = importlib.import_module('google.appengine.api.urlfetch_errors')

def hire_fetcher(module='requests', deadline=30, cache_timeout=60, cookie_timeout=3600*48, cookie_path=None):
    mod = module.split('.')[-1]
    return globals()[mod.capitalize()](importlib.import_module(module), deadline, cache_timeout, cookie_timeout, cookie_path)


class Response(object):

    def __init__(self, url, response):
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

    def __init__(self, module, deadline=30, cache_timeout=60,
                 cookie_timeout=0, cookie_path=None):
        self.set_config(module, deadline, cache_timeout, cookie_timeout, cookie_path)
        self.current_response = None

    def get_config(self):
        return dict(module=self.module,
                    deadline=self.deadline,
                    cache_timeout=self.cache_timeout,
                    cookie_timeout=self.cookie_timeout,
                    cookie_path=self.cookie_path)

    def set_config(self, module, deadline, cache_timeout, cookie_timeout, cookie_path):
        self.module = module
        self.timeout = cache_timeout
        self.cookie_timeout = cookie_timeout
        self.deadline = deadline
        self.cookie_path = cookie_path

    def fetch(self, url, payload=None, forced_update=False, cached=True, **kwargs):
        url = ud.Url(url) if type(url) is not ud.Url else url
        key = caching.create_key(ud.Url(url.text).update_query(payload).text if payload else url.text)
        if cached:
            func = caching.cache.cached(timeout=self.timeout,
                                        key_prefix=key,
                                        forced_update=lambda:forced_update)(self.cacheable_fetch)
        else:
            func = self.cacheable_fetch
        return func(url, payload=payload, key=key, **kwargs)

    def cacheable_fetch(self, url, referer=None, headers=None, key=None, **kwargs):
        r = None
        for _ in range(2):
            try:
                r = self._fetch(url,
                                deadline=self.deadline,
                                headers=self._get_headers(url, referer, headers),
                                **kwargs)
            except httplib.BadStatusLine:
                GathermateException.trace_error()
            except Exception as e:
                GathermateException.trace_error()
                if type(e) in self._get_retry_exceptions():
                    log.warning('Retry fetching...')
                    continue
                log.error('%s, while fetching [%s]', e.message, url.text)
            break
        if r:
            r.key = key
            log.debug('%s%s %d %s',
                url.netloc,
                url.path[:5] + '...' + url.path[-12:] if url.path and len(url.path) > 20 else url.path,
                r.status_code,
                tb.size_text(len(r.content) if r.content else 0))
            self._handle_response(url, r)
        return r

    def _get_headers(self, url, referer, headers):
        new_headers = { k: v for k, v in self.HEADERS.iteritems() }
        if referer:
            new_headers['referer'] = referer
        if headers:
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
        self.current_response = r
        self.url = url.text
        status_code = str(r.status_code)
        if status_code[0] in ['4', '5']:
            log.error('Destination URL not working.\n' +
                      'URL: %s\n' % url.text +
                      'Content size: %d\n' % (len(r.content) if r.content else 0) +
                      'Status Code: %d\n' % r.status_code +
                      'Headers: %s' % r.headers)
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
            log.warning('%s : %s', e, e.message)
        if tostring:
            return cookie
        else:
            return Cookie.SimpleCookie(str(cookie))

    @classmethod
    def set_cookie(cls, cookie, url, path=None):
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
                with open(cls.get_cookie_file(url, path), 'w+' ) as f:
                    f.write(cookies)
            else:
                caching.cache.set(cls.get_cookie_key(url), cookies, timeout=0)
        except Exception as e:
            log.warning(e.message)

    @classmethod
    def reset_cookie(cls, url, path=None):
        url = ud.Url(url) if type(url) is str else url
        if path is not None:
            os.remove(cls.get_cookie_file(url, path))
        else:
            key = Fetcher.get_cookie_key(url)
            caching.cache.delete(key)

    def _fetch(self, url, method='GET', payload=None, deadline=30, headers=None, follow_redirects=False):
        raise NotImplementedError

    def _get_retry_exceptions(self):
        raise NotImplementedError

class Requests(Fetcher):

    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # Override
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

    def _get_retry_exceptions(self):
        # Override
        return [self.module.exceptions.ConnectionError, self.module.exceptions.ChunkedEncodingError]

class Urlfetch(Fetcher):
    #google.appengine.api.urlfetch_errors.DeadlineExceededError
    def __init__(self, module, deadline=30, cache_timeout=60,
                 cookie_timeout=0, cookie_path=None):
        Fetcher.__init__(self, module, deadline, cache_timeout, cookie_timeout, cookie_path)

    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # Override
        if method.upper() == 'JSON':
            payload = json.dumps(payload)
            headers['Content-Type'] = 'application/json'
            method = 'POST'
        else:
            payload = ud.unsplit_qs(payload)
        try:
            r = self.module.fetch(
                url.text,
                deadline=deadline,
                payload=payload,
                method=method.upper(),
                headers=headers,
                follow_redirects=follow_redirects)
        except urlfetch_errors.DeadlineExceededError as dee:
            log.error(dee.message)
            return None
        r.url = r.final_url if r.final_url else url.text
        return Response(url.text, r)

    def _get_retry_exceptions(self):
        # Override
        return []
