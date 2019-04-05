# -*- coding: utf-8 -*-

import json
import logging
import re
import random
import time
import Cookie
import datetime
import base64
import string

import m3u8
from Crypto.Cipher import DES3

from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException
from apps.streamate.streamer import HlsStreamer
from apps.streamate.streamer import Channel

log = logging.getLogger(__name__)

def register():
    return 'Streamer', Tving


class Tving(HlsStreamer):

    API_KEY = dict(pc='1e7952d0917d6aab1f0293a063697610',
                   mobile='4263d7d76161f4a19a9efe9ca7903ec4',
                   app='56dc890767ec858dcb4abf184c0b2d2d')
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

    JQUERY_VERSION_REGEXP = re.compile(r'jquery.((\d{1,3}\.)+\d)\.min\.js', re.I)
    API_JSONP_REGEXP = re.compile(r'jquery\d+_\d+\((\{.*\})\)', re.I)
    LOGIN_OK_REGEXP = re.compile(r'\([\'\"]LOGIN_OK[\'"]\)')
    ZZANG_REGEXP = re.compile(r'var zzang = ["\'](.+)["\'];')

    streaming_instance = None

    def __init__(self,
                 fetcher,
                 mapped_channels=[],
                 except_channels=[],
                 qualities=[],
                 id=None,
                 pw=None,
                 login_type=20):
        HlsStreamer.__init__(self, fetcher, mapped_channels, except_channels, qualities)
        self.user_id = id
        self.user_pw = pw
        self.login_type = login_type
        if self.get_cache('pcid') is None:
            self.set_cookie(self.make_pcid_cookie())
        if bool(self.should_login()):
            self.login()

    def _get_channels(self, pageNo):
        channels = []
        hasNext =True
        safe_counter = 10
        while hasNext and safe_counter > 0:
            results, hasNext = self.api_channels(pageNo)
            if results is None:
                break
            for item in results:
                cid = [item.get('live_code')]
                channel = item['schedule']['channel']
                free = True if channel['free_yn'] == 'Y' else False
                #log.debug('%s -  broadcast_type: %s, channel_type: %s, free: %s', channel['name']['ko'], channel['broadcast_type'], channel['type'], free)
                cookies = self.get_cookie()
                #USER_PAY_TYPE : free=U, piad=?
                if cid[0] in self.except_channels \
                    or (not free and cookies.get('USER_PAY_TYPE').value == 'U'):
                    continue
                name = [channel['name']['ko']]
                logo = 'http://image.tving.com%s' % channel['image'][-1]['url'] if channel['image'] else ''
                mapped_cid, mapped_channel = self._get_mapped_channel('tving', cid[0])
                if mapped_channel:
                    cid.append(mapped_cid)
                    name.append(mapped_channel.get('name'))
                channels.append(
                    Channel(
                        dict(streamer='Tving',
                             cid=cid,
                             chnum=mapped_channel.get('chnum') if mapped_channel else 0,
                             name=name,
                             logo=mapped_channel.get('logo') if mapped_channel else logo,
                        )
                    )
                )
            pageNo += 1
            safe_counter -= 1
        return sorted(channels, key=lambda item: item.name), hasNext, pageNo

    def get_playlist_url(self, cid, qIndex):
        quality = self.get_quality(qIndex)
        broad_url, play_seconds, broadcast_type = self.api_streaminfo(cid, quality)
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
        if broadcast_type == 'CPSE0300':
            return broad_url, play_seconds
        else:
            response = self.fetch(url, referer=self.PLAYER_URL % cid)
            variant = m3u8.loads(response.content)
            return ud.join(url.text, variant.playlists[0].uri), play_seconds

    def get_quality(self, index):
        try:
            return self.qualities[int(index)]
        except Exception as e:
            log.error(e.message)
            return self.qualities[-1]

    def make_jsonp_name(self):
        jq_version = self.get_cache('jquery_version', '1.12.3')
        return 'jQuery' + re.sub(r'\D', '', jq_version + repr(random.random())) + '_' + str(int(time.time()*1000))

    def make_pcid_cookie(self):
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

    '''
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
    '''

    def api_streaminfo(self, cid, stream_code):
        url = ud.Url(self.API_URL + '/media/stream/info')
        key = int(time.time()*1000)
        url.update_query(dict(
            apiKey=self.API_KEY.get('pc'),
            noCache=key,
            teleCode=self.CS.get('teleCode'),
            screenCode=self.CS.get('screenCode'),
            streamCode=stream_code,
            callingFrom='FLASH',
            networkCode=self.CS.get('networkCode'), osCode=self.CS.get('osCode'),
            info='y',
            mediaCode=cid))
        r = self.fetch(url, referer=self.PLAYER_URL % cid)
        js = json.loads(r.content)
        block = True if js['body']['content']['info']['schedule']['broadcast_url'][0]['block_yn'] == 'Y' else False
        if js['body']['stream']:
            stream_url = self.decrypt(key, cid, js['body']['stream']['broadcast']['broad_url'])
        else:
            log.debug('Is this channel blocked? : %s', block)
            raise MyFlaskException('Stream URL is not available : %s', cid)
        broadcast_type = js['body']['content']['info']['schedule']['channel']['broadcast_type']
        if broadcast_type == 'CPSE0300':
            server_time = self.get_datetime(js['body']['server']['time'])
            start_time = self.get_datetime(js['body']['content']['broadcast_start_date'])
            play_seconds = (server_time - start_time).total_seconds()
        else:
            play_seconds = 0
        return stream_url, play_seconds, broadcast_type

    def decrypt(self, key, media_code, value):
        key = base64.b64decode('Y2podip0dmluZyoqZ29vZC8=') + media_code[3:] + '/' + str(key)
        cipher = DES3.new(key[:24])
        decrypted = cipher.decrypt(base64.b64decode(value))
        return filter(string.printable.__contains__, decrypted)

    def get_datetime(self, value):
        return datetime.datetime.strptime(str(value), '%Y%m%d%H%M%S')

    def api_channels(self, pageNo):
        url = ud.Url(self.API_URL + '/media/lives')
        url.update_query(dict(
            free='all', adult='all', guest='all', scope='all', order='rating', apiKey=self.API_KEY.get('pc'),
            pageNo=pageNo, pageSize=20, screenCode=self.CS.get('screenCode'),
            networkCode=self.CS.get('networkCode'), osCode=self.CS.get('osCode'),
            teleCode=self.CS.get('teleCode')
        ))
        r = self.fetch(url, referer='http://www.tving.com/live/list/top', cached=True)
        js = json.loads(r.content)
        return js['body']['result'], True if js['body']['has_more'] == 'Y' else False

    def login(self):
        payload = dict(userId=self.user_id,
                       password=self.user_pw,
                       loginType=self.login_type,
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
            return True
        else:
            log.debug('Login failed.')
            return False

    def should_login(self):
        my = 'http://www.tving.com/my/main'
        try:
            r = self.fetch(my, cached=True)
        except MyFlaskException as e:
            log.error(e.message)
            return True
        match = re.search(self.user_id if self.user_id else str(random.random()), r.content)
        if match:
            return False
        else:
            return True
