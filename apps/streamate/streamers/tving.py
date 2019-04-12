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
from apps.common.exceptions import GathermateException
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
                 excepted_channels=[],
                 qualities=[],
                 id=None,
                 pw=None,
                 channel_numbers_from=1000,
                 login_type=20):
        HlsStreamer.__init__(self, fetcher, mapped_channels, excepted_channels, qualities)
        self.user_id = id
        self.user_pw = pw
        self.channel_numbers_from = channel_numbers_from
        self.login_type = login_type
        if self.get_cache('pcid') is None:
            self.set_cookie(self.make_pcid_cookie())

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
                # log.debug('%s -  broadcast_type: %s, channel_type: %s, free: %s', channel['name']['ko'], channel['broadcast_type'], channel['type'], free)
                cookies = self.get_cookie()
                # USER_PAY_TYPE : free=U, piad=?
                # CPSE0300 and CPCS0100 : OCN, CGV, SUPER ACTION, TOONIVERSE
                # CPCS0100 : TV 채널, CPCS0300 : 티빙 채널,
                if cid[0] in self.excepted_channels \
                    or (not free and cookies.get('USER_PAY_TYPE').value == 'U') \
                    or (channel['broadcast_type'] == 'CPSE0300' and channel['type'] == 'CPCS0100') \
                    or channel['type'] == 'CPCS0300':
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
                             chnum=mapped_channel.get('chnum') if mapped_channel else int(filter(str.isdigit, str(cid[0]))) + self.channel_numbers_from,
                             name=name,
                             logo=mapped_channel.get('logo') if mapped_channel else logo,
                        )
                    )
                )
            pageNo += 1
            safe_counter -= 1
        return sorted(channels, key=lambda item: item.name), hasNext, pageNo

    def get_playlist_url(self, cid, qIndex):
        key_if_error = self.make_error_key(cid, qIndex)
        quality = self.get_quality(qIndex)
        key = int(time.time()*1000)
        js = self.api_streaminfo(cid, quality, key)
        result = js.get('body', {}).get('result', {})
        if result.get('code', '111') != '000':
            e = GathermateException(result.get('message', 'Not available') + ' : %s', cid)
            self.cache.set(key_if_error, e, timeout=self.fetcher.timeout)
            raise e
        stream = js.get('body', {}).get('stream')
        content = js.get('body', {}).get('content')
        if stream:
            stream_url = self.decrypt(key, cid, stream['broadcast']['broad_url'])
        else:
            e = GathermateException('Stream URL is not available : %s', cid)
            self.cache.set(key_if_error, e, timeout=self.fetcher.timeout)
            raise e
        channel_type = content['info']['schedule']['channel']['type']
        if channel_type == 'CPCS0300':
            server_time = self.get_datetime(js['body']['server']['time'])
            start_time = self.get_datetime(content['broadcast_start_date'])
            play_seconds = (server_time - start_time).total_seconds()
        else:
            play_seconds = 0
        stream_url = ud.Url(stream_url)
        cf_key = stream_url.query_dict.get('Key-Pair-Id')
        if cf_key is not None:
            cf_cookie = 'CloudFront-Key-Pair-Id={key}; ' \
                        'CloudFront-Policy={policy}; ' \
                        'CloudFront-Signature={sign};' \
                        .format(key=cf_key,
                                policy=stream_url.query_dict.get('Policy'),
                                sign=stream_url.query_dict.get('Signature'))
            self.set_cookie(cf_cookie)
        if channel_type == 'CPCS0300':
            return stream_url.text, play_seconds
        else:
            response = self.fetch(stream_url, referer=self.PLAYER_URL % cid)
            variant = m3u8.loads(response.content)
            return ud.join(stream_url.text, variant.playlists[0].uri), play_seconds

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

    def api_streaminfo(self, cid, stream_code, noCache):
        url = ud.Url(self.API_URL + '/media/stream/info')
        url.update_query(dict(
            apiKey=self.API_KEY.get('pc'),
            noCache=noCache,
            teleCode=self.CS.get('teleCode'),
            screenCode=self.CS.get('screenCode'),
            streamCode=stream_code,
            callingFrom='FLASH',
            networkCode=self.CS.get('networkCode'), osCode=self.CS.get('osCode'),
            info='y',
            mediaCode=cid))
        return json.loads(self.fetch(url, referer=self.PLAYER_URL % cid).content)

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
            pageNo=pageNo, pageSize=20, screenCode=self.CS.get('screenCode'), channelType='CPCS0100',
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
        if str(r.status_code)[0] in ['4', '5']:
            self._login_failed(r.url)
        if self.LOGIN_OK_REGEXP.search(r.content) is not None:
            log.debug('Login succeeded.')
            match = self.JQUERY_VERSION_REGEXP.search(r.content)
            if match is not None:
                self.set_cache('jquery_version', match.group(1))
        else:
            self._login_failed(r.url)

    def should_login(self):
        my = 'http://www.tving.com/my/main'
        r = self.fetch(my, cached=True)
        match = re.search(self.user_id if self.user_id else str(random.random()), r.content)
        if match:
            return False
        else:
            return True
