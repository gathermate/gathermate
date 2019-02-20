# -*- coding: utf-8 -*-

import json
import logging
import re
import random
import time
import Cookie
import datetime

import m3u8

from apps.common import urldealer as ud
from apps.streamate.streamer import Streamer
from apps.streamate.streamer import Channel
from apps.common.exceptions import MyFlaskException

log = logging.getLogger(__name__)

def register():
    return 'Streamer', Tving


class Tving(Streamer):

    API_KEY = '1e7952d0917d6aab1f0293a063697610'
    API_URL = 'http://api.tving.com/v1'
    BASE_URL = 'http://m.tving.com'
    LOGIN_URL = 'https://user.tving.com/user/doLogin.tving'
    LOGIN_REFERER = 'https://user.tving.com/user/login.tving?returnUrl=http%3A%2F%2Fm.tving.com%2F'
    PLAYER_URL = 'http://m.tving.com/live/%s'
    CACHE_KEY = 'tving-data'
    CS = {
        # 모바일 CSSD0200, PC CSSD0100
        'screenCode': 'CSSD0100',
        'networkCode': 'CSND0900',
        'osCode': 'CSOD0900',
        'teleCode': 'CSCD0900',
        'channelType': 'CPCS0100'
    }
    QUALITY = ['stream25', 'stream30', 'stream40', 'stream50']
    JQUERY_VERSION_REGEXP = re.compile(r'jquery.((\d{1,3}\.)+\d)\.min\.js', re.I)
    API_JSONP_REGEXP = re.compile(r'jquery\d+_\d+\((\{.*\})\)', re.I)
    LOGIN_OK_REGEXP = re.compile(r'\([\'\"]LOGIN_OK[\'"]\)')
    ZZANG_REGEXP = re.compile(r'var zzang = ["\'](.+)["\'];')

    def __init__(self, config):
        self.config = config
        self.settings = config.get('TVING')
        if self.get_cache('pcid') is None:
            self.set_cookie(self._make_pcid_cookie())
        cookies = self.get_cookie()
        if cookies.get('_tving_token') is None or self.get_cache('zzang') is None:
            self.login()

    def get_channels(self):
        result = self.api_channels()
        channels = []
        for item in result:
            channel = item['schedule']['channel']
            program = item['schedule']['program']
            name = channel['name']['ko']
            free = True if channel['free_yn'] == 'Y' else False
            drm = True if channel['drm_multi_yn'] == 'Y' else False
            if drm:
                # log.debug('%s would be excluded by drm_multi_yn.', name)
                continue
            if (not free and self.get_cache('pay_type') == 'U'):
                # log.debug('%s would be excluded by pay_type.', name)
                continue
            if name.startswith('CH.'):
                # log.debug('%s would be excluded by no live channel.', name)
                continue
            channels.append(
                Channel(
                    dict(streamer='Tving',
                         id=item.get('live_code'),
                         name=name,
                         cProgram=program['name']['ko'],
                         thumbnail='http://stillshot.tving.com/thumbnail/' + item['live_code'] + '_0_320x180.jpg')))
        del result
        return channels

    def get_segments(self, cid, url):
        response = self.fetch(url, referer=self.PLAYER_URL % cid)
        chunk = m3u8.loads(response.content)
        if chunk.is_variant:
            response = self.fetch(ud.join(response.url, chunk.playlists[0].uri), referer=self.PLAYER_URL % cid)
        return self.proxy_m3u8(cid, response.content, response.url).dumps(), response.status_code

    def get_streams(self, cid):
        streams = []
        for index in range(len(self.QUALITY)):
            url = self._get_stream_url(cid, index)
            response = self.fetch(url, referer=self.PLAYER_URL % cid)
            streams.append([index, m3u8.loads(response.content), response])
        for s in streams:
            for playlist in s[1].playlists:
                if s[0] is 0:
                    playlist.uri = 'stream?q=0'
                else:
                    playlist.uri = 'stream?q=%d' % s[0]
                    streams[0][1].add_playlist(playlist)
        response = streams[0][2]
        return streams[0][1].dumps(), response.status_code

    def get_stream(self, cid, qIndex):
        last = self.get_cache('last_stream', {})
        if last.get('quality') == qIndex:
            url = last.get('url')
        else:
            url = self._get_stream_url(cid, qIndex)
            self.set_cache('last_stream', dict(quality=qIndex, url=url.text))
        return self.get_segments(cid, url)

    def _get_stream_url(self, cid, qIndex):
        quality = self.get_quality(qIndex)
        broad_url = self.api_streamlist(cid, quality)
        url = ud.Url(broad_url)
        cf_key = url.query_dict.get('Key-Pair-Id')
        if cf_key is not None:
            cf_cookie = 'CloudFront-Key-Pair-Id={key}; ' \
                        'CloudFront-Policy={policy}; ' \
                        'CloudFront-Signature={sign};' \
                        .format(key=cf_key,
                                policy=url.query_dict.get('Policy'),
                                sign=url.query_dict.get('Signature'))
            self.set_cookie(cf_cookie)
        return url

    def _make_jsonp_name(self):
        jq_version = self.get_cache('jquery_version', '1.12.3')
        return 'jQuery' + re.sub(r'\D', '', jq_version + repr(random.random())) + '_' + str(int(time.time()*1000))

    def _make_pcid_cookie(self):
        value = str(int(time.time()*1000))
        for _ in range(10):
            value += repr(random.random())[2]
        self.set_cache('pcid', value)
        cookie = Cookie.SimpleCookie()
        name = 'PCID'
        cookie[name] = value
        cookie[name].update(dict(path='/',
                                 domain='.tving.com',
                                 expires=datetime.datetime(2100, 1, 1).strftime("%a, %d-%b-%Y %H:%M:%S GMT")))
        return cookie

    def api_streamlist(self, cid, stream_code):
        ooc = 'height=1^isPrimary=true^pointerId=1^pointerType=mouse^pressure=0^tiltX=0^tiltY=0^twist=0^width=1^altKey=false^button=0^buttons=0^clientX=239^clientY=93^ctrlKey=false^layerX=170^layerY=93^metaKey=false^movementX=0^movementY=0^offsetX=31^offsetY=35^pageX=239^pageY=93^screenX=239^screenY=207^shiftKey=false^which=1^x=239^y=93^detail=1^bubbles=true^cancelBubble=false^cancelable=true^defaultPrevented=true^eventPhase=2^isTrusted=true^returnValue=false^timeStamp=69351.9603^type=click^AT_TARGET=2^BUBBLING_PHASE=3^CAPTURING_PHASE=1^NONE=0^'
        self.set_cookie('onClickEvent2=%s; Path=/; Domain=.tving.com' % ud.quote(ooc))
        url = 'http://m.tving.com/stream/live/info.tving'
        payload = dict(mediaCode=cid,
                       streamCode=stream_code,
                       platform='',
                       olang=self.get_cache('zzang', ''),
                       ooc=ooc)
        r = self.fetch(url, method='POST', referer=self.PLAYER_URL % cid, payload=payload)
        return json.loads(r.content)['stream']['broadcast']['broad_url']

    def api_channels(self):
        url = '{api_url}/media/lives?callback={callback}' \
              '&pageNo={pageNo}&pageSize={pageSize}&order={order}&adult={adult}' \
              '&free={free}&guest={guest}&scope={scope}' \
              '&screenCode={screenCode}&networkCode={networkCode}' \
              '&osCode={osCode}&teleCode={teleCode}&apiKey={apiKey}' \
              '&_={now}'.format(api_url=self.API_URL,
                                callback=self._make_jsonp_name(),
                                pageNo=1,
                                pageSize=300,
                                order='rating',
                                adult='all', free='all', guest='all', scope='all',
                                channelType=self.CS.get('channelType', 'CPCS0100'),
                                screenCode=self.CS.get('screenCode', 'CSSD0100'),
                                networkCode=self.CS.get('networkCode', 'CSND0900'),
                                osCode=self.CS.get('osCode', 'CSOD0900'),
                                teleCode=self.CS.get('teleCode', 'CSCD0900'),
                                apiKey=self.API_KEY,
                                now=str(int(time.time()*1000)))
        r = self.fetch(url, referer='http://www.tving.com/live/list/top')
        match = self.API_JSONP_REGEXP.search(r.content)
        if match is not None:
            return json.loads(match.group(1).strip())['body']['result']
        return json.loads(r.content)['body']['result']

    def api_channel(self, channel):
        url3 = 'http://api.tving.com/v1/media/episodes?callback=jQuery11230563746359782114_1550323845035&pageNo=1&pageSize=18&order=new&adult=all&free=all&guest=all&scope=all&channelCode=C01582&lastFrequency=y&programBroadState=CPBS0200&screenCode=CSSD0100&networkCode=CSND0900&osCode=CSOD0900&teleCode=CSCD0900&apiKey=1e7952d0917d6aab1f0293a063697610&_=1550323845036'
        '''
        payload GET
        callback: jQuery11230563746359782114_1550323845035
        pageNo: 1
        pageSize: 18
        order: new
        adult: all
        free: all
        guest: all
        scope: all
        channelCode: C01582
        lastFrequency: y
        programBroadState: CPBS0200
        screenCode: CSSD0100
        networkCode: CSND0900
        osCode: CSOD0900
        teleCode: CSCD0900
        apiKey: 1e7952d0917d6aab1f0293a063697610
        _: 1550323845036
        '''
        url = 'http://api.tving.com/v1/media/stream/info?osCode=CSOD0900&apiKey=1e7952d0917d6aab1f0293a063697610&noCache=1550323850175&teleCode=CSCD0900&screenCode=CSSD0100&callingFrom=FLASH&networkCode=CSND0900&info=y&mediaCode=C01582'
        '''
        payload GET
        osCode: CSOD0900
        apiKey: 1e7952d0917d6aab1f0293a063697610
        noCache: 1550323850175
        teleCode: CSCD0900
        screenCode: CSSD0100
        callingFrom: FLASH
        networkCode: CSND0900
        info: y
        mediaCode: C01582
        '''

        url2 = 'http://api.tving.com/v1/media/live//C01582?osCode=CSOD0900&apiKey=1e7952d0917d6aab1f0293a063697610&noCache=1550323850175&teleCode=CSCD0900&screenCode=CSSD0100&callingFrom=FLASH&option=next&networkCode=CSND0900'
        '''
        payload GET
        osCode: CSOD0900
        apiKey: 1e7952d0917d6aab1f0293a063697610
        noCache: 1550323850175
        teleCode: CSCD0900
        screenCode: CSSD0100
        callingFrom: FLASH
        option: next
        networkCode: CSND0900
        '''

    def login(self):
        payload = dict(userId=self.settings.get('ID', ''),
                       password=self.settings.get('PW', ''),
                       loginType=self.settings.get('LOGIN_TYPE', 10),
                       autoLogin='on',
                       pnsToken='',
                       pocType='',
                       deviceId='',
                       kaptcha='',
                       returnUrl='')
        r = self.fetch(self.LOGIN_URL, method='POST', payload=payload, referer=self.LOGIN_REFERER)
        if self.LOGIN_OK_REGEXP.search(r.content) is not None:
            log.debug('Login succeeded.')
            match = self.JQUERY_VERSION_REGEXP.search(r.content)
            if match is not None:
                self.set_cache('jquery_version', match.group(1))
            cookies = self.get_cookie()
            self.set_cache('pay_type', cookies.get('USER_PAY_TYPE').value)
            if self.get_cache('zzang') is None:
                response = self.fetch(self.BASE_URL)
                match = self.ZZANG_REGEXP.search(response.content)
                if match is not None:
                    self.set_cache('zzang', match.group(1))
            return True
        else:
            log.debug('Login failed.')
            return False

    def check_login(self):
        my = 'http://www.tving.com/my/main'
        r = self.fetch(my)
        match = re.search(self.settings.get('ID', str(random.random())), r.content)
        if match:
            return True
        else:
            return False
