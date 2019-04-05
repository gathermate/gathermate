# -*- coding: utf-8 -*-
import re
import json
import logging

import m3u8

from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException
from apps.streamate.streamer import HlsStreamer
from apps.streamate.streamer import Channel

log = logging.getLogger(__name__)

def register():
    return 'Streamer', Pooq


class Pooq(HlsStreamer):

    BASE_URL = 'https://www.pooq.co.kr/'
    API_URL = 'https://apis.pooq.co.kr'
    PLAYER_URL = 'https://www.pooq.co.kr/player/live.html?channelid=%s'
    LOGIN_REFERER = 'https://www.pooq.co.kr/member/login.html?referer=http%3A%2F%2Fwww.pooq.co.kr%2Findex.html'
    CACHE_KEY = 'pooq-data'
    API_QUERY = dict(
        apikey='E5F3E0D30947AA5440556471321BB6D9',
        device='pc',
        partner='pooq',
        region='kor',
        targetage='auto',
        credential='none',
        pooqzone='none',
        drm='wm')

    streaming_instance = None

    def __init__(self,
                 fetcher,
                 mapped_channels=[],
                 except_channels=[],
                 qualities=[],
                 id=None,
                 pw=None):
        HlsStreamer.__init__(self, fetcher, mapped_channels, except_channels, qualities)
        self.user_id = id
        self.user_pw = pw
        if bool(self.should_login()):
            self.api_login()

    def _get_channels(self, page):
        js = self.api_channels(page)
        channels = []
        for genres in js.get('list'):
            for channel in genres.get('list'):
                cid = [channel.get('channelid')]
                if int(channel.get('price')) is 1 or cid[0] in self.except_channels:
                    continue
                name = [channel.get('channelname')]
                mapped_cid, mapped_channel = self._get_mapped_channel('pooq', cid[0])
                if mapped_channel:
                    cid.append(mapped_cid)
                    name.append(mapped_channel.get('name'))
                channels.append(
                    Channel(
                        dict(streamer='Pooq',
                             cid=cid,
                             chnum=mapped_channel.get('chnum') if mapped_channel else int(filter(str.isdigit, str(cid[0]))),
                             name=name,
                             logo=mapped_channel.get('logo') if mapped_channel else channel.get('tvimage'),
                        )
                    )
                )

        return sorted(channels, key=lambda item: item.name), False, 0

    def get_playlist_url(self, cid, qIndex):
        '''
        If you are authorized for streams, AWS Policy allows you
        to access them while 6 hours. If not, only 10 minutes.
        '''
        js = self.api_streamlist(cid, self.qualities[-1])
        url = js.get('playurl')
        aws_cookie = js.get('awscookie')
        if aws_cookie is not None:
            self.set_cookie(aws_cookie)
        response = self.fetch(url, referer=self.PLAYER_URL % cid)
        variant = m3u8.loads(response.content)
        return ud.join(url, variant.playlists[-1 if qIndex >= len(variant.playlists) else qIndex].uri), 0

    def api_ip(self):
        api = ud.Url(ud.join(self.API_URL, '/ip'))
        return self.request_api(api)

    def api_guid(self):
        api = ud.Url(ud.join(self.API_URL, '/guid/issue'))
        guid = self.request_api(api).get('guid')
        self.set_cache('guid', guid)
        return guid

    def api_channel(self, cid):
        api = ud.Url(ud.join(self.API_URL, '/live/channels/%s' % cid))
        return self.request_api(api, referer=self.PLAYER_URL % cid)

    def api_streamlist(self, cid, quality):
        api = ud.Url(ud.join(self.API_URL, '/streaming'))
        guid = self.get_cache('guid')
        if guid is None:
            guid = self.api_guid()
        query = dict(contentid=cid,
                     contenttype='live',
                     action='hls',
                     quality=quality,
                     deviceModelId='Windows 10',
                     guid=guid,
                     lastplayid='',
                     authtype='cookie',
                     isabr='y',
                     ishevc='n')
        return self.request_api(api, referer=self.PLAYER_URL % cid, query=query)

    def api_channels(self, page):
        '''
        amount = 12
        offset = 0 if page is 1 else page * amount
        api = ud.Url(ud.join(self.API_URL, '/live/popular-channels'))
        query = dict(genre='all', type='all', free='all', offset=offset, limit=amount)
        return self.request_api(api, query=query, referer=self.BASE_URL, cached=True)
        '''
        api = ud.Url(ud.join(self.API_URL, '/live/genrechannels'))
        query = dict(free='all')
        return self.request_api(api, query=query, referer=self.BASE_URL, cached=True)

    def should_login(self):
        cookies = self.get_cookie()
        if cookies.get('cs') is None:
            return True
        self.API_QUERY['credential'] = json.loads(ud.unquote(cookies.get('cs').value)).get('credential')
        try:
            self.api_user()
        except MyFlaskException as e:
            log.debug(e.message)
            return True
        return False

    def api_login(self):
        api = ud.Url(ud.join(self.API_URL, '/login'))
        api.update_query(self.API_QUERY)
        #self.fetch(api, method='OPTIONS', referer=self.LOGIN_REFERER)
        payload = dict(type='general',
                       id=self.user_id,
                       password=self.user_pw,
                       pushid='none',
                       profile='')
        response = self.fetch(api, method='JSON', payload=payload, referer=self.LOGIN_REFERER)
        js = json.loads(response.content)
        credential = js.get('credential')
        self.API_QUERY.update(credential=credential)
        self.set_cookie('cs=%s' % ud.quote(json.dumps(js)))

    def api_user(self):
        api = ud.Url(ud.join(self.API_URL, '/user'))
        api.update_query(self.API_QUERY)
        api = re.sub('/user', '//user', api.text)
        self.fetch(api, referer=self.BASE_URL, cached=True)

    def request_api(self, url, query=None, referer=None, cached=False):
        url.update_query(self.API_QUERY)
        if query is not None:
            url.update_query(query)
        response = self.fetch(url, referer=referer or self.BASE_URL, cached=cached)
        return json.loads(response.content)
