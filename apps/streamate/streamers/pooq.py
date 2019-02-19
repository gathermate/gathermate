# -*- coding: utf-8 -*-
import re
import json
import logging
import datetime

from apps.common import urldealer as ud
from apps.streamate.streamer import Streamer
from apps.streamate.streamer import Channel

log = logging.getLogger(__name__)

def register():
    return 'Streamer', Pooq


class Pooq(Streamer):

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
        self.API_QUERY['credential'] = self.get_cache('credential', 'none')
        for index in range(2):
            credential = self.API_QUERY['credential']
            if credential == 'none' or credential is None:
                if index is 2:
                    log.warning('login failed.')
                    break
                self.api_login()
            else:
                break

    def get_channels(self):
        js = self.api_channels()
        channels = []
        for channel in js.get('list'):
            channels.append(
                Channel(
                    dict(streamer='Pooq',
                         id=channel.get('channelid'),
                         name=channel.get('channelname'),
                         cProgram=channel.get('title'),
                         thumbnail=channel.get('image'))
                )
            )
        return channels

    def get_playlist(self, cid, url):
        response = self.fetch(url, referer=self.PLAYER_URL % cid)
        response.content = self.proxy_m3u8(cid, response.content, url).dumps()
        return response

    def get_streamlist(self, cid):
        js = self.api_streamlist(cid)
        playurl = js.get('playurl')
        self.set_cookie(js.get('awscookie'))
        response = self.fetch(playurl,
                              referer=self.PLAYER_URL % cid)
        response.content = self.proxy_m3u8(cid, response.content, response.url).dumps()
        return response

    def check_login(self):
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
        js = self.request_api(api)
        guid = js.get('guid')
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

    def api_streamlist(self, cid):
        api = ud.Url(ud.join(self.API_URL, '/streaming'))
        guid = self.get_cache('guid')
        if guid is None:
            guid = self.api_guid()
        query = dict(contentid=cid,
                     contenttype='live',
                     action='hls',
                     quality='480p',
                     deviceModelId='Windows 10',
                     guid=guid,
                     lastplayid='',
                     authtype='cookie',
                     isabr='y',
                     ishevc='n')
        js = self.request_api(api, referer=self.PLAYER_URL % cid, query=query)
        self.set_cache('awscookie', js.get('awscookie'))
        return js

    def api_channels(self):
        api = ud.Url(ud.join(self.API_URL, '/live/all-channels'))
        query = dict(genre='all', type='all', free='all', offset=0, limit=999)
        return self.request_api(api, query=query, referer=self.PLAYER_URL % 'K01')

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
        self.set_cache('credential', credential)
        self.API_QUERY.update(credential=credential)
        self.set_cookie('cs=%s' % ud.quote(json.dumps(js)))
        return js

    def request_api(self, url, query=None, referer=None):
        if query is not None:
            temp = dict(self.API_QUERY, **query)
            url.update_query(temp)
        else:
            url.update_query(self.API_QUERY)
        if referer is None:
            referer = self.BASE_URL
        response = self.fetch(url, referer=referer)
        return json.loads(response.content)

    # pooq loggging data sample
    BOOKMARK_DATA = dict(
        itemType=3,
        userNo=0,
        profileId=0,
        playId='',
        guid='',
        cornerId='',
        channelType='L',
        contentId='',
        programId='K02',
        deviceType=1,
        ipAddress='',
        concurrencyGroup=1,
        issue='',
        isCharged='n',
        priceType='n',
        pooqzoneType='',
        logType='I',
        extra=dict(osV='Windows 10', appV='1.1.6', apiV=3),
        isABR='Y',
        BR=1000,
        mediaTime='00:00:30',
        logDate='2019-02-13 12:47:27+0900')
