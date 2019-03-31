# -*- coding: utf-8 -*-
import re
import json
import logging
import time

import m3u8
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA
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

    streaming_instance = None

    def __init__(self,
                 fetcher,
                 mapped_channels=[],
                 except_channels=[],
                 qualities=[],
                 id=None,
                 pw=None,
                 login_type=None):
        HlsStreamer.__init__(self, fetcher, mapped_channels, except_channels, qualities)
        self.user_id = id
        self.user_pw = pw
        self.login_type = login_type
        if self.should_login():
            self.login()

    @property
    def playlist_url(self):
        return self._playlist_url + '?%s' % self._get_epoch_time()

    @playlist_url.setter
    def playlist_url(self, v):
        self._playlist_url = v

    def _get_epoch_time(self):
        return int(time.time()*1000)

    def _get_channels(self, pageNo):
        url = 'http://www.oksusu.com/api/live/organization/list?genreCode=99&orgaPropCode=ALL'
        r = self.fetch(url, referer='http://www.oksusu.com/live?mid=9000000399', headers=self.HEADERS)
        js = json.loads(r.content)
        channels = []
        for ch in js['channels']:
            cid = [ch['serviceId']]
            #channelProd : {free: "0", loginFree: "5", basicFree: "20", paid: "99"}
            #log.debug('%s : %s', ch['channelName'], ch['hlsUrlPhoneFixSD'])
            if cid[0] in self.except_channels \
                or ch['stopByCopyrightYn'] == 'Y' \
                or ch['stop_broadcast_yn'] == 'Y' \
                or int(ch['channelProd']) >= 20 \
                or ch['hlsUrlPhoneFixSD'] is None:
                continue
            name = [ch['channelName']]
            mapped_channel = self._get_mapped_channel('oksusu', cid[0])
            if mapped_channel:
                    cid.append(mapped_channel.get('cid'))
                    name.append(mapped_channel.get('name'))
            channels.append(
                Channel(
                    dict(streamer='Oksusu',
                         cid=cid,
                         chnum=mapped_channel.get('chnum') if mapped_channel else 0,
                         name=name,
                         logo=mapped_channel.get('logo') if mapped_channel else 'http://image.oksusu.com:8080/thumbnails/image/0_0_F20/live/logo/387/%s' % ch['channelImageName'],
                    )
                )
            )
        return sorted(channels, key=lambda item: item.name), False, pageNo

    def get_playlist_url(self, cid, qIndex):
        r = self.fetch(self.PLAYER_URL % cid, referer=self.PLAYER_URL % cid)
        match = re.search(r'contentsInfo:\s(.+)\s\|', r.content)
        if match:
            js = json.loads(match.group(1))
            response = self.fetch(js['streamUrl']['urlAUTO'], referer=self.PLAYER_URL % cid)
            variant = m3u8.loads(response.content)
            variant.playlists = sorted(variant.playlists, key=lambda x: x.stream_info[0])
            return variant.playlists[-1 if qIndex >= len(variant.playlists) else qIndex].uri

    def login(self):
        if self.login_type == 'tid':
            self.login_by_tid(self.user_id, self.user_pw)


    def should_login(self):
        r = self.fetch(self.LOGIN_CHECK_URL, referer=self.BASE_URL)
        match = re.search(r'isLogin:\s(.+),', r.content)
        if match and match.group(1) == 'true':
            log.debug('############ is login? %s', match.group(1))
            return False
        return True

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
        r = self.fetch('https://auth.skt-id.co.kr/auth/api/v1/keys.do', method='POST', payload={'valueType': 'hex'}, referer=referer)
        js = json.loads(r.content)
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
        r = self.fetch('https://auth.skt-id.co.kr/auth/type/login/loginProcess.do', method='POST', follow_redirects=True, payload=data, referer=referer)
        '''
        for iframe in etree.HTML(r.content).xpath('//iframe'):
            self.fetch(iframe.get('src'))
        '''
        url = ud.Url('http://sktsso.tworld.co.kr/createsubcookie.jsp')
        url.update_query({'mode':'check'})
        #response = self.fetch(url, referer=referer)
        match = re.search('location\.href=\"(.+)\";', r.content)
        if match:
            #auth/type/login/callbaskSSOCompleted.do
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
            r = self.fetch('https://www.oksusu.com/user/login', payload=payload, method='POST', referer='https://www.oksusu.com/user/login?rw=%2Fmy', follow_redirects=True)




#for testing

if __name__ == '__main__':

    import json

    import app
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_v1_5
    from Crypto.Hash import SHA
    from lxml import etree

    from apps.common import fetchers
    FETCHER = {
        'MODULE': 'requests',
        'CACHE_TIMEOUT': 60,
        'DEADLINE': 60,
        'COOKIE_PATH': None,
        'COOKIE_TIMEOUT' : 0,
    }



    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 10 Build/MOB31T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }



    def get_login_ciphertext(user_id, user_pw, nonce, modulus, exponent):
        message = '%s|%s|%s' % (user_id, user_pw, nonce)
        print message

        key = RSA.construct((long(modulus, 16), long(exponent, 16)))
        cipher = PKCS1_v1_5.new(key)
        ciphertext = cipher.encrypt(message.encode('utf-8'))
        return ciphertext.encode('hex')

    def login_tid(user_id, user_pw):
        r = fetcher.fetch('https://www.oksusu.com/user/tid/login?rw=%2Fmy', headers=headers,)
        var = {}
        for match in re.finditer(r'var\s(.+)\s=\s\'(.+)\';', r.content):
            if match:
                var[match.group(1)] = match.group(2)

        query = dict(client_id=var['clientId'],
                     client_secret=var['clientSecret'],
                     redirect_uri='https://www.oksusu.com/user/tid/login?rw=%2Fmy',
                     scope=var['scope'],
                     response_type=var['responseType'],
                     state=var['state'],
                     nonce=var['nonce'],
                     client_type=var['clientType'],
                     service_type=var['serviceType'],
                     popup_request_yn=var['popup_request_yn'])

        url = ud.Url('https://auth.skt-id.co.kr/auth/authorize.do')
        url.update_query(query)
        r = fetcher.fetch(url, follow_redirects=False, headers=headers, referer='https://www.oksusu.com/user/tid/login?rw=')
        referer = r.url
        data = {}
        html = etree.HTML(r.content)

        for inp in html.xpath('//form[@id="loginForm"]/input'):
            data[inp.get('name')] = inp.get('value')


        r = fetcher.fetch('https://auth.skt-id.co.kr/auth/api/v1/keys.do', method='POST', headers=headers, payload={'valueType': 'hex'}, referer=referer)
        js = json.loads(r.content)
        print js

        data.update(dict(issuing_type=10,
                         cipher_kid=js['kid'],
                         ciphertext=get_login_ciphertext(user_id, user_pw, js['nonce'], js['n'], js['e']),
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

        print data
        print '-'*30
        r = fetcher.fetch('https://auth.skt-id.co.kr/auth/type/login/loginPreChecker.do', method='POST', headers=headers, payload=data, referer=referer)
        print '-'*30
        print r.status_code
        #print r.content
        print r.headers

        r = fetcher.fetch('https://auth.skt-id.co.kr/auth/type/login/loginProcess.do', method='POST', follow_redirects=True, headers=headers, payload=data, referer=referer)
        print '-'*30
        print r.status_code
        #print r.content
        print r.headers

        for iframe in etree.HTML(r.content).xpath('//iframe'):
            response = fetcher.fetch(iframe.get('src'))
            print response.headers

        url = ud.Url('http://sktsso.tworld.co.kr/createsubcookie.jsp')
        url.update_query({'mode':'check'})
        response = fetcher.fetch(url, referer=referer)

        match = re.search('location\.href=\"(.+)\";', r.content)
        if match:
            print '-'*30
            print match.group(1)
            referer = match.group(1)
            print '-'*30
            #auth/type/login/callbaskSSOCompleted.do
            r = fetcher.fetch(match.group(1), headers=headers, follow_redirects=False)
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
            print '####### login payload'
            print payload
            print '####### login payload'
            r = fetcher.fetch('https://www.oksusu.com/user/login', payload=payload, method='POST', referer='https://www.oksusu.com/user/login?rw=%2Fmy', follow_redirects=True)
            print '####### login response header'
            print r.headers
            print '####### login response header'
            print '####### final cookie'
            print ok.get_cookie(tostring=True)
            print '####### final cookie'
            headers.update(dict(dnt=1,
                                pragma='no-cache',
                                referer='https://www.oksusu.com/user/login'))
            r = fetcher.fetch('http://www.oksusu.com/my', follow_redirects=True)
            print r.headers
            match = re.search('isLogin:\s(.+),', r.content)
            if match and match.group(1) == 'true':
                return False
            return True



    TEST_CHANNELS = [
        dict(cid='KBS1',name='KBS 1',chnum=9,sk='5100.11',epgcokr=9,kt=9,lg=501,sky=796,pooq='K01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/9.png'),
        dict(cid='KBS2',name='KBS 2',chnum=7,sk='5100.12',epgcokr=7,kt=7,lg=502,sky=795,pooq='K02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/7.png'),
    ]
    app = app.app
    fetcher = fetchers.hire_fetcher(cookie_path=None)
    ok = Oksusu(fetcher,
                TEST_CHANNELS,
                **{k.lower(): v for k, v in app.config['STREAMATE']['STREAMERS']['Oksusu'].iteritems()})
    #r = fetcher.fetch('https://www.oksusu.com/user/tid/login?rw=/')
    #login_tid(ok.user_id, ok.user_pw)
    n = '89d2671cc2f94bb8100a79de758455a7c6bc34836b97d394e475be9e42350f3c1a87c724f98861140484ee432c3c872615f7f201ddf1beb31ec4b9967a00f73c8768aa987b63e80fe4c047a24880db216f19d1513e92447f0176c1373f0c918001ac84bb6f03fed17bacfe8e06abff8e62cda100036c62eeac685155bc64c25d34423652348c45e187c76295aeda1cec4ded760657274f62db772c77994e159982fb7a91fe74fb49751b57cbcc6a423d06a970dcae6501c19250fd2039b30d6233ccd4001c123d043577f0df89f6eaff21b38174b66ee59f046b3b89dcc522adacc49b34ac1e458098eeae0585c0cef428a661b4515c8b861dd850b46532c5c1'
    e = '10001'


    ok.get_playlist_url(241, 0)



