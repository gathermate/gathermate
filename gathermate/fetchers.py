# -*- coding: utf-8 -*-

import Cookie
import json
import logging as log
import httplib

from util.cache import cache
from util import urldealer as ud

class Response(object):
    '''
    for avoid cache error : PicklingError: Can't pickle httplib.HTTPMessage: it's not the same object as httplib.HTTPMessage
    '''
    def __init__(self, headers, content, code, url, final_url):
        # type: (Dict[Text, Text], str, int, Text, Text) -> None
        self.headers = headers
        self.content = content
        self.status_code = code
        self.url = url
        self.final_url = final_url

class Fetcher(object):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
    }

    cum_size = 0.0
    UNITS = {
        'byte': 1.0,
        'KB': 1024.0,
        'MB': 1024.0 ** 2,
        'GB': 1024.0 ** 3,
    }

    COOKIE_ATTRS = ['expires', 'path', 'comment', 'domain', 'max-age', 'secure', 'version', 'httponly']
    THRESHOLD = 50

    def __init__(self, config, module):
        # type : (Dict[Text, Union[Text, str, int]], Callable) -> None
        self.config = config
        self.module = module
        self.SECRET_KEY = config.get('SECRET_KEY')
        self.timeout = config.get('CACHE_TIMEOUT')
        self.cookie_timeout = config.get('COOKIE_TIMEOUT')
        self.deadline = config.get('DEAD_LINE', 30)
        self.counter = 0
        log.debug('Using {} for Fetcher.'.format(type(self).__name__))

    def _create_key(self, url, payload):
        # type: (urldealer.URL, Dict[Text, Text]) -> Text
        key_suffix = '{}?{}'.format(url.text, ud.unsplit_qs(payload)) if payload else url.text
        return '{}-{}'.format(self.SECRET_KEY, key_suffix)

    def fetch(self, url, referer=None, method='GET', payload=None, forced_update=False):
        # type: (urldealer.URL, str, str, Dict[Text, Text], bool) -> Response
        self.counter += 1
        if self.counter > self.THRESHOLD:
            log.error('Fetching counter exceeds threshold by a request. : %d of %d', self.counter, self.THRESHOLD)
            raise Exception('Too many fetchings by a request.')

        key = self._create_key(url, payload)
        @cache.cached(timeout=self.timeout, key_prefix=key, forced_update=lambda:forced_update)
        def cached_fetch():
            # type: () -> Response
            log.debug('This fetching will update its cache.')

            log.debug('Fetching [...{0}{1}]'
                      .format(url.path, '?%s' % url.query if url.query else ''))

            r = self._fetch(url,
                            deadline=self.deadline,
                            payload=payload,
                            method=method,
                            headers=self._get_headers(url, referer),
                            follow_redirects=True)

            current_size = len(r.content)
            self.cum_size += current_size
            log.debug('Fetched {0:s} from [...{1}{2}]'
                      .format(self.size_text(current_size),
                              url.path,
                              '?%s' % url.query if url.query else ''))

            self._handle_response(url, r)

            return r

        return cached_fetch()

    def _get_headers(self, url, referer):
        # type: (urldealer.URL, Text) -> Dict[Text, Text]
        headers = {}
        for k, v in self.headers.items():
            headers[k] = v
        headers['referer'] = referer
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
        status_code = str(r.status_code)
        if status_code[0] in ['4', '5']:
            raise Exception('''
                Destination URL not working.
                Content size: %d,
                Status Code: %d,
                Headers: %s''' % (len(r.content), r.status_code, r.headers))

        self.url = url.text
        #self.final_url = r.final_url

        set_cookie = r.headers.get('set-cookie')
        if set_cookie:
            key = u'{}-{}-cookies'.format(self.SECRET_KEY, url.netloc)
            self._set_cookie(key, set_cookie)

    def _get_cookie(self, url):
        # type: (urldealer.URL) -> Text
        key = u'{}-{}-cookies'.format(self.SECRET_KEY, url.netloc)
        cookie = cache.get(key)
        if cookie:
            return cookie
        return Cookie.SimpleCookie().output(self.COOKIE_ATTRS, header='', sep=';')

    def _set_cookie(self, key, new_cookie):
        # type: (Text, cookie.SimpleCookie) -> None
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

        '''
        When calling response.text() and no encoding was set or determined,
        requests relies on chardet to detect the encoding.
        Unfortunately, chardet can be pathologically slow and memory-hungry to do its job.

        The encoding of the response content is determined based solely on HTTP headers,
        following RFC 2616 to the letter. If you can take advantage of non-HTTP knowledge to
        make a better guess at the encoding, you should set r.encoding appropriately
        before accessing this property.
        '''
        return Response(r.headers, r.content, r.status_code, url.text, r.url)

class Urlfetch(Fetcher):

    # Override
    def _fetch(self, url, deadline=30, method='GET', payload=None, headers=None, follow_redirects=False):
        # type: (urldealer.URL, int, str, Dict[Text, Text], Dict[Text, Text], bool) -> Response

        if payload:
            payload = ud.unsplit_qs(payload)

        try:
            r = self.module.fetch(
                url.text,
                deadline=deadline,
                payload=payload,
                method='POST' if method.upper() == 'JSON' else method,
                headers=headers,
                follow_redirects=follow_redirects)
        except httplib.BadStatusLine as e:
            log.error('{}'.format(e.message))


        r.url = r.final_url if r.final_url else url.text
        return Response(r.headers, r.content, r.status_code, url.text, r.url)
