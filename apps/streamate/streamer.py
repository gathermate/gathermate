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

    def fetch(self, url, cached=False, **kwargs):
        response = fetchers.hire_fetcher(self.config['FETCHER']).fetch(url, cached=cached, **kwargs)
        if str(response.status_code).startswith('2'):
            return response
        else:
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
        fetchers.Fetcher.set_cookie(value, url or self.BASE_URL, path=self.config.get('FETCHER', {}).get('COOKIE_PATH', None))

    def get_cookie(self, tostring=False):
        return fetchers.Fetcher.get_cookie(self.BASE_URL, tostring=tostring, path=self.config.get('FETCHER', {}).get('COOKIE_PATH', None))

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
                    if not self.should_stream:
                        break
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

    @property
    def genre(self):
        return self.get('genre')

'''
- tvg-id is value of '<channel id="">' in EPG xml file. If the tag is absent then addon will use tvg-name for map channel to EPG;
- tvg-name is value of display-name in EPG there all space chars replaced to _ (underscore char) if this value is not found in xml then addon will use the channel name to find correct EPG.
- tvg-logo is name of channel logo file. If this tag is absent then addon will use channel name to find logo.
- tvg-shift is value in hours to shift EPG time. This tag can be used in #EXTM3U for apply shift to all channels or in #EXTINF for apply shift only to current channel.
- group-name is channels group name. If the tag is absent then addon will use group name from the previous channel.
'''