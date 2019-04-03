# -*- coding: utf-8 -*-

import logging
import json
import time

import m3u8

from apps.common import caching
from apps.common.datastructures import MultiDict
from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException

log = logging.getLogger(__name__)


class Streamer(object):

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def fetch(self, url, cached=False, **kwargs):
        response = self.fetcher.fetch(url, cached=cached, **kwargs)
        if str(response.status_code)[0] in ['2', '3']:
            return response
        else:
            log.debug(response.headers)
            raise MyFlaskException("Couldn't fetch : %s", url, response=response)

    def get_cache(self, key, default=None):
        cached = self.get_caches()
        return cached.get(key, default)

    def get_caches(self):
        cached = caching.cache.get(caching.create_key(self.CACHE_KEY))
        return json.loads(str(cached)) if cached is not None else {}

    def set_cache(self, key, value, timeout=0):
        cached = self.get_caches()
        cached[key] = value
        caching.cache.set(caching.create_key(self.CACHE_KEY), json.dumps(cached), timeout=timeout)

    def set_cookie(self, value, url=None):
        self.fetcher.set_cookie(value, url or self.BASE_URL, path=self.fetcher.cookie_path)

    def get_cookie(self, tostring=False):
        return self.fetcher.get_cookie(self.BASE_URL, tostring=tostring, path=self.fetcher.cookie_path)

    def get_resource(self, url):
        r = self.fetch(url, referer=self.BASE_URL)
        return r.content, r.status_code, dict(r.headers)


class HlsStreamer(Streamer):

    def __init__(self, fetcher, mapped_channels, except_channels, qualities):
        Streamer.__init__(self, fetcher)
        self.mapped_channels = mapped_channels
        self.except_channels = except_channels
        self.qualities = qualities
        self.playlist = {}
        self.should_stream = True

    def streaming(self, cid, qIndex):
        '''
        Allows only one request.
        '''
        if self.__class__.streaming_instance is not None:
            self.__class__.streaming_instance.should_stream = False
        self.__class__.streaming_instance = self
        self.playlist_url = self.get_playlist_url(cid, qIndex)
        duration, play_sequence = self.set_playlist(cid, 0)
        while self.should_stream:
            if len(self.playlist) > 0:
                try:
                    url = self.playlist.pop(play_sequence)
                except KeyError:
                    play_sequence = sorted(self.playlist.iteritems(), key=lambda tuple_:tuple_[0])[0][0]
                    url = self.playlist.pop(play_sequence)
                if self.should_stream:
                    yield self.fetch(url, referer=self.PLAYER_URL % cid).content
                    play_sequence += 1
            else:
                for _ in range(int(duration)):
                    if not self.should_stream:
                        break
                    time.sleep(1)
                if self.should_stream:
                    duration = self.set_playlist(cid, play_sequence)[0]

    def set_playlist(self, cid, play_sequence):
        playlist = m3u8.loads(self.fetch(self.playlist_url, referer=self.PLAYER_URL % cid).content)
        media_sequence = playlist.media_sequence
        for segment in playlist.segments:
            if media_sequence >= play_sequence and media_sequence not in self.playlist:
                self.playlist[media_sequence] = ud.join(self.playlist_url, segment.uri)
            media_sequence += 1
        return playlist.target_duration, playlist.media_sequence

    def get_channels(self):
        page = 1
        has_next = True
        safe_counter = 50
        while has_next and safe_counter > 0:
            channels, has_next, page = self._get_channels(page)
            page += 1
            for channel in channels:
                yield channel
            safe_counter -= 1

    def _get_mapped_channel(self, streamer, scid):
        return next(((cid, ch) for cid, ch in self.mapped_channels.iteritems() if str(ch.get(streamer)) == str(scid)), None)

    def get_playlist_url(self):
        raise NotImplementedError

    def _get_channels(self):
        raise NotImplementedError


class Channel(MultiDict):

    @property
    def streamer(self):
        return self.get('streamer')

    @property
    def cid(self):
        return self.get('cid')

    @property
    def name(self):
        return self.get('name')

    @property
    def logo(self):
        return self.get('logo')

    @property
    def chnum(self):
        return self.get('chnum')
