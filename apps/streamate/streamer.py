# -*- coding: utf-8 -*-

import logging
import time
import datetime
from datetime import datetime as dt
from collections import deque
from functools import wraps

import m3u8

from apps.common import caching
from apps.common.datastructures import MultiDict
from apps.common import urldealer as ud
from apps.common.exceptions import GathermateException
from apps.streamate.views import name as app_name

log = logging.getLogger(__name__)


class Streamer(object):

    def __init__(self, fetcher):
        self.fetcher = fetcher

    @property
    def cache(self):
        return caching.cache

    def fetch(self, url, cached=False, callback=None, **kwargs):
        r = self.fetcher.fetch(url, cached=cached, **kwargs)
        if callback:
            return callback(r)
        return r

    def make_error_key(self, *args):
        key_list = [app_name, self.__class__.__name__.lower()] + list(args)
        return caching.make_error_key(key_list)

    def get_cache(self, key, default=None):
        cached = self.get_caches()
        return cached.get(key, default)

    def get_caches(self):
        return caching.cache.get(caching.create_key(self.CACHE_KEY)) or {}

    def set_cache(self, key, value, timeout=0):
        cached = self.get_caches()
        cached[key] = value
        caching.cache.set(caching.create_key(self.CACHE_KEY), cached, timeout=timeout)

    def set_cookie(self, value, url=None):
        self.fetcher.set_cookie(value, url or self.BASE_URL, path=self.fetcher.cookie_path)

    def get_cookie(self, tostring=False):
        return self.fetcher.get_cookie(self.BASE_URL, tostring=tostring, path=self.fetcher.cookie_path)

    def get_resource(self, url):
        r = self.fetch(url, referer=self.BASE_URL)
        return r.content, r.status_code, dict(r.headers)


def login_required(func):
    @wraps(func)
    def check_login(self, *args, **kwargs):
        if self.user_id is None or self.user_id == '' \
           or self.user_pw is None or self.user_pw == '':
           raise GathermateException('Check your ID and Password of %s.', self.__class__.__name__)
        if self.should_login():
            self.login()
        return func(self, *args, **kwargs)
    return check_login


class HlsStreamer(Streamer):

    def __init__(self, fetcher, mapped_channels, excepted_channels, qualities):
        Streamer.__init__(self, fetcher)
        self.mapped_channels = mapped_channels
        self.excepted_channels = excepted_channels
        self.qualities = qualities
        self.should_stream = True

    @login_required
    def streaming(self, cid, qIndex):
        '''
        Allows only one request.
        Spoof HLS Player.
        '''
        if self.__class__.streaming_instance is not None:
            self.__class__.streaming_instance.should_stream = False
        self.__class__.streaming_instance = self
        referer = self.PLAYER_URL % cid
        key_if_error = self.make_error_key(cid, qIndex)
        playlist_url, played_seconds = self.get_playlist_url(cid, qIndex)
        playlist = self.get_playlist(playlist_url, referer, 0, played_seconds, key_if_error)
        played_time = dt.now()
        play_sequence = 0
        while self.should_stream:
            if len(playlist) > 0:
                segment = playlist.popleft()
                if self.should_stream:
                    yield self.fetch(segment.uri, referer=referer).content
                    played_time += datetime.timedelta(seconds=segment.duration)
                    play_sequence = segment.sequence
                if len(playlist) is 0 and playlist.is_endlist:
                    sleep_time = int((played_time - dt.now()).total_seconds()) - segment.duration
                elif played_time - dt.now() > datetime.timedelta(seconds=int(segment.duration*2)):
                    sleep_time = int(segment.duration)
                else:
                    sleep_time = 0
                for count in range(sleep_time, 0, -1):
                    if not self.should_stream:
                        break
                    time.sleep(1)
            else:
                if playlist.is_endlist:
                    playlist_url, played_seconds = self.get_playlist_url(cid, qIndex)
                    play_sequence = 0
                else:
                    play_sequence += 1
                    played_seconds = 0
                if self.should_stream:
                    playlist = self.get_playlist(playlist_url, referer, play_sequence, played_seconds)
                if len(playlist) is 0:
                    play_sequence -= 1
                    time.sleep(segment.duration*2)

    def get_playlist(self, playlist_url, referer, play_sequence, played_seconds, key_if_error):
        r = self.fetch(playlist_url, referer=referer)
        m3u = m3u8.loads(r.content)
        playlist = Playlist(is_endlist=m3u.is_endlist)
        if len(m3u.segments) is 0:
            e = GathermateException("The fetched playlist is empty.")
            log.error(e.message)
            self.should_stream = False
            self.cache.set(key_if_error, e, timeout=self.fetcher.timeout)
            return playlist
        cumulative_time = 0
        for sequence, segment in enumerate(m3u.segments, m3u.media_sequence):
            cumulative_time += segment.duration
            if played_seconds > cumulative_time:
                continue
            if sequence >= play_sequence:
                segment.uri = ud.join(playlist_url, segment.uri)
                segment.sequence = sequence
                playlist.append(segment)
        if len(playlist) is 0:
            log.debug("No new item, %s is required but %s was given.", play_sequence, m3u.media_sequence + len(m3u.segments) - 1)
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

    def _login_failed(self, message):
        raise GathermateException('Login failed : %s', message)

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


class Playlist(deque):

    def __init__(self, is_endlist=False):
        deque.__init__(self)
        self._is_endlist = is_endlist

    @property
    def is_endlist(self):
        return self._is_endlist

    @is_endlist.setter
    def is_endlist(self, v):
        self._is_endlist = bool(v)
