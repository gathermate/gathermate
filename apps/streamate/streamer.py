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

    def set_cookie(self, value, url=None):
        if url is None:
            url = self.BASE_URL
        fetchers.Fetcher.set_cookie(value, url, path=self.config['FETCHER']['COOKIE_PATH'])

    def get_cookie(self, tostring=False):
        return fetchers.Fetcher.get_cookie(self.BASE_URL, tostring=tostring, path=self.config['FETCHER']['COOKIE_PATH'])

    def get_resource(self, url):
        r = self.fetch(url, referer=self.BASE_URL)
        return r.content, r.status_code, dict(r.headers)


class HlsStreamer(Streamer):

    def streaming(self, cid, qIndex):
        '''
        Allows only one request.
        '''
        if self.__class__.streaming_instance is not None:
            self.__class__.streaming_instance.should_stream = False
        self.__class__.streaming_instance = self
        self.playlist_url = self.get_playlist_url(cid, qIndex)
        duration, play_sequence = self.set_playlist(cid, qIndex, 0)
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
                    time.sleep(1)
                    yield ''
                if self.should_stream:
                    duration = self.set_playlist(cid, qIndex, play_sequence)[0]

    def set_playlist(self, cid, qIndex, play_sequence):
        playlist = m3u8.loads(self.fetch(self.playlist_url, referer=self.PLAYER_URL % cid).content)
        media_sequence = playlist.media_sequence
        for segment in playlist.segments:
            if media_sequence >= play_sequence and media_sequence not in self.playlist:
                self.playlist[media_sequence] = ud.join(self.playlist_url, segment.uri)
            media_sequence += 1
        return playlist.target_duration, playlist.media_sequence

    def should_login(self):
        cached_should_login = caching.cache.cached(
            timeout=60*60,
            key_prefix=caching.create_key(self.CACHE_KEY) + '-should_login')(self._should_login)
        return cached_should_login()

    def get_channels_m3u(self):
        channel_list = []
        page = 1
        has_next = True
        while has_next:
            channels, has_next, page = self.get_channels(page)
            channel_list += channels
            page += 1
        return self.make_m3u(channel_list)

    def make_m3u(self, channels):
        m3u = '#EXTM3U\n'
        #EXTINF:-1 tvg-id="103" tvg-logo="로고url" tvh-chnum="1" tvh-tags="연예/오락",KBS 드라마
        for channel in channels:
            m3u += '#EXTINF:-1 tvg-id="{}" tvg-logo="None" tvh-chnum="None",{}\n'.format(channel.id, channel.name)
            url_for = self.config.get('URL_FOR')
            url = url_for('.channel_streaming',
                          _external=True,
                          streamer=self.__class__.__name__.lower(),
                          cid=channel.id)
            m3u += url + '\n'
        return m3u


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
