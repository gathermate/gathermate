# -*- coding: utf-8 -*-

import logging
import json
import time

import m3u8

from apps.common import fetchers
from apps.common import caching
from apps.common.datastructures import MultiDict
from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException

log = logging.getLogger(__name__)


class Streamer(object):

    def fetch(self, url, **kwargs):
        response = fetchers.hire_fetcher(config=self.config).fetch(url, cached=False, **kwargs)
        if str(response.status_code).startswith('2'):
            return response
        else:
            raise MyFlaskException("Couldn't fetch : %s", url, response=response)

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


class HlsStreamer(Streamer):

    playlist = {}

    def streaming(self, cid, qIndex):
        duration, play_sequence = self.set_playlist(cid, qIndex, 0)
        while True:
            if len(self.playlist) > 0:
                try:
                    url = self.playlist.pop(play_sequence)
                except KeyError:
                    play_sequence = sorted(self.playlist.iteritems(), key=lambda tuple_:tuple_[0])[0][0]
                    url = self.playlist.pop(play_sequence)
                yield self.fetch(url, referer=self.PLAYER_URL % cid).content
                play_sequence += 1
            else:
                time.sleep(duration)
                duration = self.set_playlist(cid, qIndex, play_sequence)[0]

    def set_playlist(self, cid, qIndex, play_sequence):
        url = self.get_playlist_url(cid, qIndex)
        playlist = m3u8.loads(self.fetch(url, referer=self.PLAYER_URL % cid).content)
        media_sequence = playlist.media_sequence
        for segment in playlist.segments:
            if media_sequence >= play_sequence and media_sequence not in self.playlist:
                self.playlist[media_sequence] = ud.join(url, segment.uri)
            media_sequence += 1
        return playlist.target_duration, playlist.media_sequence

    @caching.cache.memoize(timeout=60*60*5)
    def get_playlist_url(self, cid, qIndex):
        return self._get_playlist_url(cid, qIndex)


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

    @property
    def logo(self):
        return self.get('logo')

    @property
    def chnum(self):
        return self.get('chnum')

