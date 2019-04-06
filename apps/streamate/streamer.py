# -*- coding: utf-8 -*-

import logging
import json
import time
import datetime
from datetime import datetime as dt
from collections import deque

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
        return self.fetcher.fetch(url, cached=cached, **kwargs)

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
        self.should_stream = True

    def streaming(self, cid, qIndex):
        '''
        Allows only one request.
        Spoof HLS Player.
        '''
        if self.__class__.streaming_instance is not None:
            self.__class__.streaming_instance.should_stream = False
        self.__class__.streaming_instance = self
        referer = self.PLAYER_URL % cid
        playlist_url, play_seconds = self.get_playlist_url(cid, qIndex)
        playlist = self.get_playlist(playlist_url, referer, 0, play_seconds)
        buffering_time = dt.now()
        error_count = 0
        is_endlist = False
        last_segment_duration = 0
        play_sequence = 0
        while self.should_stream and error_count < 5:
            if len(playlist) > 0:
                segment = playlist.popleft()
                if segment != 'ENDLIST':
                    if self.should_stream:
                        r = self.fetch(segment.uri, referer=referer)
                        yield r.content
                        if not str(r.status_code).startswith('2'):
                            error_count += 1
                        play_sequence = segment.sequence
                        last_segment_duration = segment.duration
                        buffering_time += datetime.timedelta(seconds=segment.duration)
                    buffered = buffering_time - dt.now()
                    if buffered > datetime.timedelta(seconds=int(segment.duration*3)):
                        sleep_time = int(segment.duration)
                    else:
                        sleep_time = 0
                else:
                    sleep_time = int((buffering_time - dt.now()).total_seconds()) - last_segment_duration
                    is_endlist = True
                for count in range(sleep_time, 0, -1):
                    if not self.should_stream:
                        break
                    time.sleep(1)
            else:
                if is_endlist:
                    playlist_url, play_seconds = self.get_playlist_url(cid, qIndex)
                    play_sequence = 0
                else:
                    play_sequence += 1
                    play_seconds = 0
                if self.should_stream:
                    playlist = self.get_playlist(playlist_url, referer, play_sequence, play_seconds)
                    if len(playlist) is 0:
                        self.should_stream = False

    def get_playlist(self, playlist_url, referer, play_sequence, play_seconds):
        m3u = m3u8.loads(self.fetch(playlist_url, referer=referer).content)
        playlist = deque()
        cumulative_time = 0
        for sequence, segment in enumerate(m3u.segments, m3u.media_sequence):
            cumulative_time += segment.duration
            if play_seconds > cumulative_time:
                continue
            if sequence >= play_sequence:
                segment.uri = ud.join(playlist_url, segment.uri)
                segment.sequence = sequence
                playlist.append(segment)
        if m3u.is_endlist and len(playlist) > 0:
            playlist.append('ENDLIST')
        return playlist

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
        return next(((cid, ch) for cid, ch in self.mapped_channels.iteritems() if str(ch.get(streamer)) == str(scid)), (None, None))

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
