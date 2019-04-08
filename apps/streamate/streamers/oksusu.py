# -*- coding: utf-8 -*-

import re
import json
import logging
import time

import m3u8
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from lxml import etree

from apps.common import urldealer as ud
from apps.common.exceptions import MyFlaskException
from apps.streamate.streamer import HlsStreamer
from apps.streamate.streamer import Channel

log = logging.getLogger(__name__)

def register():
    return 'Streamer', Oksusu


class Oksusu(HlsStreamer):
    BASE_URL = 'https://www.oksusu.com'
    LOGIN_CHECK_URL = 'http://www.oksusu.com/my'
    PLAYER_URL = 'http://www.oksusu.com/v/%s'
    HEADERS = {'X-Requested-With': 'XMLHttpRequest'}
    CACHE_KEY = 'oksusu-data'

    streaming_instance = None

    def __init__(self,
                 fetcher,
                 mapped_channels=[],
                 excepted_channels=[],
                 qualities=[],
                 id=None,
                 pw=None,
                 channel_numbers_from=1000,
                 login_type=None):
        HlsStreamer.__init__(self, fetcher, mapped_channels, excepted_channels, qualities)
        self.user_id = id
        self.user_pw = pw
        self.channel_numbers_from = channel_numbers_from
        self.login_type = login_type
        if self.should_login():
            self.login()

    def _get_epoch_time(self):
        return int(time.time()*1000)

    def _get_channels(self, pageNo):
        url = 'http://www.oksusu.com/api/live/organization/list?genreCode=99&orgaPropCode=ALL'
        r = self.fetch(url, referer='http://www.oksusu.com/live?mid=9000000399', headers=self.HEADERS)
        js = json.loads(r.content)
        channels = []
        ticket_info = self.get_cache('user-ticket-info')
        point_info = self.get_cache('user-point-info')
        coupon_info = self.get_cache('user-coupon-info')
        log.debug('Bill INFO: %s / %s / %s', ticket_info, point_info ,coupon_info)
        for ch in js['channels']:
            cid = [ch['serviceId']]
            #channelProd : {free: "0", loginFree: "5", basicFree: "20", paid: "99"}
            #log.debug('%s : %s', ch['channelName'], ch['hlsUrlPhoneFixSD'])
            if cid[0] in self.excepted_channels \
                or ch['stopByCopyrightYn'] == 'Y' \
                or ch['stop_broadcast_yn'] == 'Y' \
                or int(ch['channelProd']) >= 20 \
                or ch['blackout_yn'] == 'Y':
                continue
            name = [ch['channelName']]
            mapped_cid, mapped_channel = self._get_mapped_channel('oksusu', cid[0])
            if mapped_channel:
                cid.append(mapped_cid)
                name.append(mapped_channel.get('name'))
            channels.append(
                Channel(
                    dict(streamer='Oksusu',
                         cid=cid,
                         chnum=mapped_channel.get('chnum') if mapped_channel else int(filter(str.isdigit, str(cid[0]))) + self.channel_numbers_from,
                         name=name,
                         logo=mapped_channel.get('logo') if mapped_channel else 'http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/%s' % ch['channelImageName'],
                    )
                )
            )
        return sorted(channels, key=lambda item: item.name), False, pageNo

    def get_playlist_url(self, cid, qIndex):
        key_if_error = 'get_playlist_url-%s-%s-error' % (cid, qIndex)
        self.was_error_before(self.get_cache(key_if_error))
        r = self.fetch(self.PLAYER_URL % cid, referer=self.PLAYER_URL % cid)
        match = re.search(r'contentsInfo:\s(.+)\s\|', r.content)
        if match:
            js = json.loads(match.group(1))
            if js is None:
                self.set_cache(key_if_error, True, timeout=60)
                raise MyFlaskException("JSON is None.")
            urlAUTO = js['streamUrl']['urlAUTO']
            nvodUrlList = js['streamUrl']['nvodUrlList']
            if urlAUTO:
                response = self.fetch(urlAUTO, referer=self.PLAYER_URL % cid)
                variant = m3u8.loads(response.content)
                variant.playlists = sorted(variant.playlists, key=lambda x: x.stream_info[0])
                return ud.join(urlAUTO, variant.playlists[-1 if qIndex >= len(variant.playlists) else qIndex].uri + '?%s' % self._get_epoch_time()), 0
            elif nvodUrlList:
                nvod_token = nvodUrlList[0]['nvod_token']
                timestamp = float(js['timestamp'])/1000
                starttime = float(js['channel']['programs'][0]['startTime'])/1000
                return nvod_token, int(timestamp - starttime)
            else:
                self.set_cache(key_if_error, True, timeout=60)
                raise MyFlaskException("No available stream URL.")


    LOGIN_OKSUSU_URL = 'https://www.oksusu.com/user/login'
    def login(self):
        if self.login_type == 'tid':
            self.login_by_tid(self.user_id, self.user_pw)
        elif self.login_type == 'oksusu':
            payload = dict(loginMode=1, rw='/', cw='', serviceProvider='', accessToken='', userId=self.user_id, password=self.user_pw, captcha='')
            self.fetch(self.LOGIN_OKSUSU_URL, method='POST', payload=payload, referer=self.LOGIN_OKSUSU_URL + '?rw=%2F')
        else:
            pass
        if self.should_login():
            self._login_failed("should_login() still returns True")

    def should_login(self):
        r = self.fetch(self.LOGIN_CHECK_URL, referer=self.BASE_URL, cached=True)
        match = re.search(r'isLogin:\s(.+),', r.content)
        if match:
            isLogin = match.group(1)
            log.debug('Is user logged in? : %s', isLogin)
            if  isLogin == 'true':
                self.set_bill_info(r.content)
                return False
        return True

    def set_bill_info(self, content):
        for dd in etree.HTML(content).xpath('//dd[contains(@id, "user-")]'):
            self.set_cache(dd.get('id'), dd.text)

    def get_login_ciphertext(self, user_id, user_pw, nonce, modulus, exponent):
        message = '%s|%s|%s' % (user_id, user_pw, nonce)
        key = RSA.construct((long(modulus, 16), long(exponent, 16)))
        cipher = PKCS1_v1_5.new(key)
        ciphertext = cipher.encrypt(message.encode('utf-8'))
        return ciphertext.encode('hex')

    LOGIN_TID_URL = 'https://www.oksusu.com/user/tid/login?rw=%2Fmy'
    def login_by_tid(self, user_id, user_pw):
        r = self.fetch(self.LOGIN_TID_URL, referer=self.BASE_URL)
        var = {}
        for match in re.finditer(r'var\s(.+)\s=\s\'(.+)\';', r.content):
            if match:
                var[match.group(1)] = match.group(2)
        if len(var) is 0:
            self._login_failed(r.url)
        query = dict(client_id=var['clientId'],
                     client_secret=var['clientSecret'],
                     redirect_uri=self.LOGIN_TID_URL,
                     scope=var['scope'],
                     response_type=var['responseType'],
                     state=var['state'],
                     nonce=var['nonce'],
                     client_type=var['clientType'],
                     service_type=var['serviceType'],
                     popup_request_yn=var['popup_request_yn'])
        url = ud.Url('https://auth.skt-id.co.kr/auth/authorize.do')
        url.update_query(query)
        r = self.fetch(url, follow_redirects=False, referer=self.LOGIN_TID_URL)
        referer = r.url
        data = {}
        html = etree.HTML(r.content)
        for inp in html.xpath('//form[@id="loginForm"]/input'):
            data[inp.get('name')] = inp.get('value')
        if len(data) is 0:
            self._login_failed(r.url)
        r = self.fetch('https://auth.skt-id.co.kr/auth/api/v1/keys.do', method='POST', payload={'valueType': 'hex'}, referer=referer)
        js = json.loads(r.content)
        if len(js) is 0:
            self._login_failed(r.url)
        data.update(dict(issuing_type=10,
                         cipher_kid=js['kid'],
                         ciphertext=self.get_login_ciphertext(user_id, user_pw, js['nonce'], js['n'], js['e']),
                         redirect_uri=ud.quote(data['redirect_uri']),
                         transLoginyn='',
                         sdk_version='',
                         thirdPartyYn='Y',
                         force_id_pwd_login_yn='Y',
                         auto_login_yn='Y',
                         ssoLoginCheckFlag='C',
                         popup_request_yn='',
                         internal_proc_yn='',
                         login_id=''))
        r = self.fetch('https://auth.skt-id.co.kr/auth/type/login/loginPreChecker.do', method='POST', payload=data, referer=referer)
        result = json.loads(r.content)
        if result['resultCode'] != '0000':
            self._login_failed(r.url)
        r = self.fetch('https://auth.skt-id.co.kr/auth/type/login/loginProcess.do', method='POST', follow_redirects=True, payload=data, referer=referer)
        '''
        url = ud.Url('http://sktsso.tworld.co.kr/createsubcookie.jsp')
        url.update_query({'mode':'check'})
        response = self.fetch(url, referer=referer)
        '''
        match = re.search('location\.href=\"(.+)\";', r.content)
        if match:
            # ...auth/type/login/callbaskSSOCompleted.do
            r = self.fetch(match.group(1), referer=referer)
            referer = match.group(1)
            location = ud.Url(r.headers['Location'])
            fragments = ud.split_qs(location.fragment)
            payload = {
                'loginMode': 3,
                'serviceProvider': 'tid',
                'accessToken': fragments['id_token'],
                'nuguId': '',
                'userId': '',
                'password': '',
                'rw': '/my'
            }
            r = self.fetch(self.LOGIN_OKSUSU_URL, payload=payload, method='POST', referer=self.LOGIN_OKSUSU_URL + '?rw=%2Fmy', follow_redirects=True)
        else:
            self._login_failed(r.url)

    def _login_failed(self, url):
        raise MyFlaskException('Login failed at %s', url)
