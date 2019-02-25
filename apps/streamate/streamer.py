# -*- coding: utf-8 -*-

import logging
import json

import m3u8

from apps.common import fetchers
from apps.common import caching
from apps.common.datastructures import MultiDict
from apps.common import urldealer as ud

log = logging.getLogger(__name__)


class Streamer(object):

    def fetch(self, url, **kwargs):
        return fetchers.hire_fetcher(config=self.config).fetch(url, cached=False, **kwargs)

    def get_cache(self, key, default=None):
        cached = self.get_caches()
        return cached.get(key, default)

    def get_caches(self):
        cached = caching.cache.get(caching.create_key(self.CACHE_KEY))
        if cached is None:
            return {}
        return json.loads(str(cached))

    def set_cache(self, key, value, timeout=0):
        cached = self.get_caches()
        cached[key] = value
        caching.cache.set(caching.create_key(self.CACHE_KEY), json.dumps(cached), timeout=timeout)
        del cached

    def proxy_m3u8(self, cid, content, url):
        if type(url) is ud.Url:
            url = url.text
        if type(content) is not m3u8.model.M3U8:
            content = m3u8.loads(content)
        if content.is_variant:
            for playlist in content.playlists:
                # Input URL argument at the end unless encoding it.
                playlist.uri = 'segments?url={}'.format(ud.quote(ud.join(url, playlist.uri)))
        else:
            for segment in content.segments:
                segment.uri = 'segment?url={}'.format(ud.quote(ud.join(url, segment.uri)))
        return content

    def set_cookie(self, value, url=None):
        if url is None:
            url = self.BASE_URL
        fetchers.Fetcher.set_cookie(value, url, path=self.config['FETCHER']['COOKIE_PATH'])

    def get_cookie(self, tostring=False):
        return fetchers.Fetcher.get_cookie(self.BASE_URL, tostring=tostring, path=self.config['FETCHER']['COOKIE_PATH'])

    def get_resource(self, url):
        r = self.fetch(url, referer=self.BASE_URL)
        return r.content, r.status_code, dict(r.headers)

    def get_segment(self, cid, url):
        r = self.fetch(url, referer=self.PLAYER_URL % cid)
        return r.content, r.status_code, dict(r.headers)

    def get_quality(self, index):
        try:
            return self.QUALITY[int(index)]
        except Exception as e:
            log.error(e.message)
            return self.QUALITY[-1]


class Channel(MultiDict):

    @property
    def streamer(self):
        return self.get('streamer')

    @property
    def id(self):
        return self.get('id')

    @property
    def name(self):
        return self.get('name')

    @property
    def cProgram(self):
        return self.get('cProgram')

    @property
    def thumbnail(self):
        return self.get('thumbnail')

    @property
    def rating(self):
        return self.get('rating')

