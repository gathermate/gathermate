# -*- coding: utf-8 -*-
import re
import json
import logging
import datetime

import m3u8

from apps.common import urldealer as ud
from apps.streamate.streamer import HlsStreamer
from apps.streamate.streamer import Channel

log = logging.getLogger(__name__)

def register():
    return 'Streamer', Pooq


class Pooq(HlsStreamer):

    BASE_URL = 'https://www.pooq.co.kr/'
    API_URL = 'https://apis.pooq.co.kr'
    PLAYER_URL = 'https://www.pooq.co.kr/player/live.html?channelid=%s'
    LOGIN_CHECK_URL = 'https://member.pooq.co.kr/me'
    LOGIN_REFERER = 'https://www.pooq.co.kr/member/login.html?referer=http%3A%2F%2Fwww.pooq.co.kr%2Findex.html'
    JS_ALERT = re.compile(r'alert\(["\'](.+)[\'"]\)')
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

    def __init__(self, config):
        self.config = config
        self.settings = config.get('POOQ')
        if self.should_login():
            self.api_login()

    def get_channels(self, page):
        js = self.api_channels(page)
        channels = []
        for channel in js.get('list'):
            channels.append(
                Channel(
                    dict(streamer='Pooq',
                         id=channel.get('channelid'),
                         name=channel.get('channelname'),
                         cProgram=channel.get('title'),
                         thumbnail=channel.get('image'),
                         rating=channel.get('playratio'))
                )
            )
        has_next = True if js['pagecount'] > js['count'] else False
        return sorted(channels, key=lambda item: item.rating, reverse=True), has_next, page

    def _get_playlist_url(self, cid, qIndex):
        '''
        If you are authorized for streams, AWS Policy allows you
        to access them while 6 hours. If not, only 10 minutes.
        '''
        js = self.api_streamlist(cid, self.settings.get('QUALITY')[-1])
        url = js.get('playurl')
        aws_cookie = js.get('awscookie')
        if aws_cookie is not None:
            self.set_cookie(aws_cookie)
        response = self.fetch(url, referer=self.PLAYER_URL % cid)
        variant = m3u8.loads(response.content)
        if qIndex >= len(variant.playlists):
            return ud.join(url, variant.playlists[-1].uri)
        else:
            return ud.join(url, variant.playlists[qIndex].uri)

    def should_login(self):
        response = self.fetch(self.LOGIN_CHECK_URL, referer=self.BASE_URL)
        match = self.JS_ALERT.search(response.content)
        if match is not None:
            msg = match.group(1)
            if '로그인한' in msg:
                return False
        else:
            return True

    def api_ip(self):
        api = ud.Url(ud.join(self.API_URL, '/ip'))
        return self.request_api(api)

    def api_guid(self):
        api = ud.Url(ud.join(self.API_URL, '/guid/issue'))
        guid = self.request_api(api).get('guid')
        self.set_cache('guid', guid)
        return guid

    def api_channel(self, channel):
        api = ud.Url(ud.join(self.API_URL, '/live/channels/%s' % channel))
        return self.request_api(api, referer=self.PLAYER_URL % channel)

    def api_epg(self, channel):
        api = ud.Url(ud.join(self.API_URL, '/live/epgs/channels/%s' % channel))
        stime = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d %H:%M')
        etime = datetime.datetime.strftime(datetime.datetime.today() + datetime.timedelta(days=1), '%Y-%m-%d %H:%M')
        query = dict(startdatetime=stime, enddatetime=etime, offset=0, limit=999, orderby='old')
        return self.request_api(api, referer=self.PLAYER_URL % channel, query=query)

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
        js = self.request_api(api, referer=self.PLAYER_URL % cid, query=query)
        return js

    def api_channels(self, page):
        amount = 12
        offset = 0 if page is 1 else page * amount
        api = ud.Url(ud.join(self.API_URL, '/live/popular-channels'))
        query = dict(genre='all', type='all', free='all', offset=offset, limit=amount)
        return self.request_api(api, query=query, referer=self.BASE_URL)

    def api_login(self):
        api = ud.Url(ud.join(self.API_URL, '/login'))
        api.update_query(self.API_QUERY)
        self.fetch(api, method='OPTIONS', referer=self.LOGIN_REFERER)
        payload = dict(type='general',
                       id=self.settings.get('ID', ''),
                       password=self.settings.get('PW', ''),
                       pushid='none',
                       profile='')
        response = self.fetch(api, method='JSON', payload=payload, referer=self.LOGIN_REFERER)
        js = json.loads(response.content)
        credential = js.get('credential')
        self.API_QUERY.update(credential=credential)
        self.set_cookie('cs=%s' % ud.quote(json.dumps(js)))
        return js

    def api_user(self):
        api = ud.Url(ud.join(self.API_URL, '/user'))
        api.update_query(self.API_QUERY)
        response = self.fetch(api, referer=self.BASE_URL)
        return json.loads(response.content)

    def request_api(self, url, query=None, referer=None):
        url.update_query(self.API_QUERY)
        if query is not None:
            url.update_query(query)
        if referer is None:
            referer = self.BASE_URL
        response = self.fetch(url, referer=referer)
        return json.loads(response.content)
