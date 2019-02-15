# -*- coding: utf-8 -*-
import re
import json
import logging as log
import datetime

import m3u8

from apps.common import urldealer as ud
from apps.streamate.streamer import Streamer
from apps.common.cache import cache

def register():
    return 'Streamer', Pooq

class Pooq(Streamer):

    API_QUERY = dict(
        apikey='E5F3E0D30947AA5440556471321BB6D9',
        device='pc',
        partner='pooq',
        region='kor',
        targetage='auto',
        credential='none',
        pooqzone='none',
        drm='wm')

    BASE_URL = 'https://www.pooq.co.kr/'
    API_URL = 'https://apis.pooq.co.kr'
    PLAYER_URL = 'https://www.pooq.co.kr/player/live.html?channelid=%s'
    M3U8_URL = 'https://live-k02.cdn.pooq.co.kr/hls/K02/1/1000/live.m3u8?seek=0&buffer=10'
    LOGIN_CHECK_URL = 'https://member.pooq.co.kr/me'
    LOGIN_REFERER = 'https://www.pooq.co.kr/member/login.html?referer=http%3A%2F%2Fwww.pooq.co.kr%2Findex.html'
    JS_ALERT = re.compile(r'alert\(["\'](.+)[\'"]\)')
    CACHE_KEY = 'pooq-data'

    def __init__(self, config, query):
        self.config = config
        self.API_QUERY['credential'] = self.get_cache().get('login', {}).get('credential', 'none')
        self.CHANNEL = query.get('channel', '')
        self.PLAYLIST = query.get('list', '')
        self.MEDIA = query.get('media', '')
        self.RESOURCE = query.get('resource', '')


    def proxy(self):
        '''
        API flow
        url : https://www.pooq.co.kr/player/live.html?channelid=K01
        login > ip > guid > alarms-new > uiservice/notices > live/channels/K01 > live/epgs/channels/K01
        > live/all-channels > uiservice/zzim/channel > vod/relatedcontents(K01) > vod/relatedcontents(K01_T2000-0054)
        > live/channels/K01 > streaming > m3u8 > media > bookmark(log interval 10s) > media ...
        > live/channels/K01 (next program starts)
        '''
        for index in range(2):
            if self.API_QUERY['credential'] == 'none' or self.API_QUERY['credential'] is None:
                if index is 2:
                    return 'login failed.'
                self.api_login()
            else:
                break
        if self.MEDIA:
            log.debug('Proxy this media : %s', self.MEDIA)
            return self.handle_media(self.MEDIA)
        if self.PLAYLIST:
            log.debug('Proxy this playlist : %s', self.PLAYLIST)
            response = self.fetch(self.PLAYLIST, referer=self.PLAYER_URL % self.CHANNEL)
            return self.handle_playlist(response)
        if self.CHANNEL == 'all':
            log.debug('All channels...')
            js = self.api_all_channels()
            '''
            for item in js.get('list'):
                item.get('image') = ud.quote(item.get('image'))
                '''
            return js
        if self.CHANNEL:
            log.debug('Fetch playlist from API.')
            js = self.api_streaming(self.CHANNEL)
            playurl = js.get('playurl')
            cookie = js.get('awscookie')
            response = self.fetch(playurl,
                                  referer=self.PLAYER_URL % self.CHANNEL,
                                  headers={'cookie': cookie})
            return self.handle_playlist(response)
        if self.RESOURCE:
            url = ud.Url(self.RESOURCE)
            log.debug('Fetch : %s', url.text)
            return self.fetch(url, referer=self.BASE_URL)
        return "Coudn't understand what you want."

    def check_login(self):
        response = self.fetch(self.LOGIN_CHECK_URL, referer=self.BASE_URL)
        match = self.JS_ALERT.search(response.content)
        if match is not None:
            msg = match.group(1)
            if '로그인한' in msg:
                return False
        else:
            return True

    def handle_playlist(self, response):
        mlist = m3u8.loads(response.content)
        if mlist.is_variant:
            for playlist in mlist.playlists:
                # Input URL argument at the end unless encoding it.
                playlist.uri = '{}?list={}'.format(self.CHANNEL,
                                                       ud.join(response.url, playlist.uri))
        else:
            for segment in mlist.segments:
                segment.uri = '{}?media={}'.format(self.CHANNEL,
                                                       ud.join(response.url, segment.uri))
        return mlist.dumps()

    def handle_media(self, url):
        url = ud.Url(url)
        response = self.fetch(url, referer=self.PLAYER_URL % self.CHANNEL)
        return response.content

    def api_ip(self):
        api = ud.Url(ud.join(self.API_URL, '/ip'))
        return self.request_api(api, cache_id='ip')

    def api_guid(self):
        api = ud.Url(ud.join(self.API_URL, '/guid/issue'))
        return self.request_api(api, cache_id='guid')

    def api_channel(self, channel):
        api = ud.Url(ud.join(self.API_URL, '/live/channels/%s' % channel))
        return self.request_api(api, referer=self.PLAYER_URL % channel)

    @cache.cached(key_prefix=cache.create_key('pooq-channels-epg'), timeout=60)
    def api_epg(self, channel):
        api = ud.Url(ud.join(self.API_URL, '/live/epgs/channels/%s' % channel))
        stime = datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d %H:%M')
        etime = datetime.datetime.strftime(datetime.datetime.today() + datetime.timedelta(days=1), '%Y-%m-%d %H:%M')
        query = dict(startdatetime=stime, enddatetime=etime, offset=0, limit=999, orderby='old')
        return self.request_api(api, referer=self.PLAYER_URL % channel, query=query)

    def api_streaming(self, channel):
        api = ud.Url(ud.join(self.API_URL, '/streaming'))
        guid = self.get_cache().get('guid', {}).get('guid', None)
        if guid is None:
            guid = self.api_guid().get('guid')
        query = dict(contentid=channel,
                     contenttype='live',
                     action='hls',
                     quality='480p',
                     deviceModelId='Windows 10',
                     guid=guid,
                     lastplayid='',
                     authtype='cookie',
                     isabr='y',
                     ishevc='n')
        return self.request_api(api, referer=self.PLAYER_URL % channel, query=query)

    @cache.cached(key_prefix=cache.create_key('pooq-all-channels'), timeout=60)
    def api_all_channels(self):
        api = ud.Url(ud.join(self.API_URL, '/live/all-channels'))
        query = dict(genre='all', type='all', free='all', offset=0, limit=999)
        return self.request_api(api, query=query, referer=self.PLAYER_URL % 'K01')

    def api_login(self):
        '''
        https://apis.pooq.co.kr/login?apikey=E5F3E0D30947AA5440556471321BB6D9&device=pc&partner=pooq&region=kor&targetage=auto&credential=none&pooqzone=none&drm=wm
        METHOD = OPTIONS
        referer: https://www.pooq.co.kr/member/login.html?referer=http%3A%2F%2Fwww.pooq.co.kr%2Findex.html
        https://apis.pooq.co.kr/login?apikey=E5F3E0D30947AA5440556471321BB6D9&device=pc&partner=pooq&region=kor&targetage=auto&credential=none&pooqzone=none&drm=wm
        second Request Method: POST
        payload : {"type":"general","id":"blunzl","pushid":"none","password":"smb400@smb400","profile":""}
        second response:
        {"credential":"5oyK+J0591jGIz+eliNXXZ40Ce83hwFgslsYLuZZGGbRUrrNBHRaED02aeOZRqArUvDtUE5czjuo0Vj7c5zrNoMqnzN9GHLoh3CLKZte/PAJ7tbr9PLhLrzgPmEci+mxwAuszzxD3e80v2hl7r5nbZRHDKLPwKXpL4bsRc0Gi7xUqzSWAJUTqbd7gdvgNXjv4v4RaQoSqa75rd9stbiGEW5raOiyFp0STnx2/Fp/XAVmSkEH4iL+sEOt4o8Z5Sz/","uno":"7673036","name":"ê¹ëì","profile":"0","type":"general","joindate":"","profilename":"íë¡í1","profilecount":"1","profileimage":"img.pooq.co.kr/service30/profile/0.png","needselectprofile":"n","needchangepassword":"n","apppush":"n","apppush_agreedate":"2018-07-24"}
        after login cookie:
        Cookie: tooltip=%7B%22live%22%3Atrue%2C%22main%22%3Atrue%2C%22vod%22%3Atrue%7D; close-popup=1; pz=%7B%22isPooqZone%22%3Afalse%7D; cs=%7B%22isPooqZone%22%3Afalse%2C%22credential%22%3A%22HlTMKnLEJK0HE7hLJDJ50OL5U4fSM3ABve8HQndoLzgWY1m8VPPOT18R2NkEj10ahhTSwoNNih28zXt2Rw78JQE86F33N60ovzIJlvuTGr6hEKcE8WjLzjj%2Bo2jHbBdQKUFIapDVZxYBBCFIQCDWee5h%2FDipxb%2BcJIURM3UcmqdawrX3rZxklX38vxJxHjOUQzhhsfWs18RuwS5kJuGaVYKUAoTQSra0VYDyMH4CDD73q9Lj2eMg4o211hLM3CyC%22%2C%22uno%22%3A%227673036%22%2C%22name%22%3A%22%EA%B9%80%EB%8F%99%EC%8B%9D%22%2C%22profile%22%3A%220%22%2C%22type%22%3A%22general%22%2C%22joindate%22%3A%22%22%2C%22profilename%22%3A%22%ED%94%84%EB%A1%9C%ED%95%841%22%2C%22profilecount%22%3A%221%22%2C%22profileimage%22%3A%22img.pooq.co.kr%2Fservice30%2Fprofile%2F0.png%22%2C%22needselectprofile%22%3A%22n%22%2C%22needchangepassword%22%3A%22n%22%2C%22apppush%22%3A%22n%22%2C%22apppush_agreedate%22%3A%222018-07-24%22%7D

        api query = credential: 5oyK%2BJ0591jGIz%2BeliNXXZ95vXN5V3e9m6OwijFuVEqqKgxEc5TPbJPryGG1ecR60vZfFBpTKPZ%2FP1oFOZgQBaLhUYKle0fMpNLN2bWjh%2FMiuX0q7LVYYRR6ITtps4v0Q6vJDfd7PoTlyiDmVhRrXOvOw9Ynrn%2BbpUXuRBObCS2FZpFsm8HgC%2BieJJbYWc9lqVOdwHNR9gUTMcxGaRiLV28vclLPON2n7NOWLj2px1pJHoQl1UtIaL1A9BSIz10f
        '''
        api = ud.Url(ud.join(self.API_URL, '/login'))
        api.update_query(self.API_QUERY)
        self.fetch(api, method='OPTIONS', referer=self.LOGIN_REFERER)
        payload = dict(type='general',
                       id=self.config['POOQ']['ID'],
                       password=self.config['POOQ']['PW'],
                       pushid='none',
                       profile='')
        response = self.fetch(api, method='JSON', payload=payload, referer=self.LOGIN_REFERER)
        js = self.caching_api(response, 'login')
        self.API_QUERY.update(credential=js.get('credential'))
        set_cookie = 'cs=%s' % ud.quote(json.dumps(js))
        self.fetch(self.BASE_URL, headers={'cookie':set_cookie}, referer=self.LOGIN_REFERER)
        return js

    def request_api(self, url, cache_id=None, query=None, referer=None):
        if query is not None:
            temp = dict(self.API_QUERY, **query)
            url.update_query(temp)
        else:
            url.update_query(self.API_QUERY)
        if referer is None:
            referer = self.PLAYER_URL % self.CHANNEL
        response = self.fetch(url, referer=referer)
        if cache_id is not None:
            return self.caching_api(response, cache_id)
        return json.loads(response.content)

    def caching_api(self, response, cache_id):
        js = json.loads(response.content)
        cached = self.get_cache()
        temp = cached.get(cache_id, {})
        temp.update(js)
        cached[cache_id] = temp
        self.set_cache(cached, timeout=0)
        return js

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

"""
API_COMMAND
    LOGIN: "login",
    STREAMING: "streaming",
    META_LIVE:"live/channels/",
    META_VOD:"vod/contents/",
    META_MOVIE:"movie/contents/",
    META_CLIP:"clip/contents/",
    QVOD_CHECK: "streaming/status",
    POST_RECOMMENDATIONS: "uiservice/recommend/contents/mostwith/",
    RECOMMENDATIONS: "recommendation/contents",
    LIST_LIVE_POPULAR: "live/popular-channels",
    LIST_VOD_POPULAR: "vod/popularcontents",
    LIST_VOD_NEW:"vod/newcontents",
    LIST_VOD_PROGRAM:"vod/programs-contents/",
    LIST_MOVIE_RECOMMEND:"movie/recommend/contents",
    LIST_MOVIE_NEW:"movie/contents",
    LIST_THEME: "themes-related-player/",
    HOME_SHOPPING: "homeshopping",
    GET_CONTENT_ID: "vod/programs-contentid/",
    GET_USER: "/user"
API_RESULT
    SUCCESS: "200",
    NETWORK_ERROR: "400",
    SERVER_ERROR: "500",
    API_ERROR: "550",
    API_RETRY: "551"
STREAMING_TYPE
    HLS: "hls",
    DASH: "dash",
    PROGRESS: "progressive",
    DOWNLOAD: "download"
STREAMING_TYPE
    NONE: "none",
    WIDEVINE_CLASIC: "wc",
    WIDEVINE: "wm",
    PLAY_READY: "pr",
    FAIR_PLAY: "fp"
SHARED_KEY
    QUALITY : "quality",
    LAST_PLAY_ID: "lastPlayID",
    LAST_GUID: "lastGUID",
    AUTO_PLAY: "autoPlay",
    PLAY_RATE: "playRate",
    SCREEN_RATIO: "screenRatio",
    UID_COOKIE: "uidCookie",
    INIT_USER:"initUser",
    TM_INFO:"tmInfo",
    AUTO_PLAY_INFO:"autoPlayInfo",
    I_WANT_FLASH: "iWantFlash",
    PLAYER_TYPE: "playerType",
    USER_NO: "userNo",
    CREDENTIAL: "credential"
PLAYER_TEC_TYPE
    FLASH: "FLASH",
    HTML5: "HTML5"
PLAYER_TYPE
    BIT_MOVIN: "10",
    FLASH: "11",
    HTML5: "12",
    VIDEO_JS: "15",
    CAST: "16"
itemType
{
    case "500":
    case "360p":
        id="1";
        break;
    case "700":
        id="2";
        break;
    case "1000":
    case "480p":
        id="3";
        break;
    case "2000":
    case "720p":
        id="4";
        break;
    case "5000":
    case "1080p":
        id="9";
        break;
    case "2160p":
        id="21";
        break;
}

getBookMarkData: function(vodObject)
    {

        var param = new Object();
        param.itemType = vodObject.getItemType();
        param.userNo = this.userNo;
        param.profileId = this.profileID;
        param.playId = this.lastPlayID;
        param.guid =  this.GUID;
        if(param.userNo=="" || param.userNo==undefined || param.userNo==null || param.userNo=="undefined") param.userNo="NOLOGIN";

        this.setBookMarkContentID(vodObject,param);
        param.deviceType = "1";
        param.ipAddress=this.clientIP;
        if(param.ipAddress=="" || param.ipAddress==undefined || param.ipAddress==null) param.ipAddress="127.0.0.0";
        param.concurrencyGroup = vodObject.concurrencyGroup;
        param.issue = vodObject.issue;
        param.isCharged = vodObject.chargedType;
        param.priceType = vodObject.priceType;
        param.pooqzoneType = (this.pooqzoneType != "none") ? "P01" : "";
        return param;

    },

"""