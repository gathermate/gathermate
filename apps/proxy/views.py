# -*- coding: utf-8 -*-

import logging as log
import json

from flask import Blueprint
from flask import request
from flask import send_from_directory
from flask import Response
from flask import stream_with_context
from flask import render_template
from flask import current_app as app

from apps.common import urldealer as ud
from apps.common import fetchers
from apps.common.datastructures import MultiDict

name = 'Proxy'

proxy = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')

@proxy.route('/', strict_slashes=False)
def index():
    return request.base_url

@proxy.route('/server/<string:fname>')
def serve(fname):
    return proxy.send_static_file('./video/%s' % fname)

@proxy.route('/<path:site>')
def proxied(site):
    query = MultiDict(request.args)
    query['server'] = request.base_url
    data = app.managers[name].request(site, query)
    if data.startswith('#EXTM3U'):
        return Response(data, mimetype='application/vnd.apple.mpegurl')
    return data

@proxy.route('/client')
def client():
    return render_template('player2.html', source=request.args.get('source'))

@proxy.route('/test')
def test():
    query = MultiDict(request.args)
    query['base_url'] = request.base_url
    api_url = 'https://apis.pooq.co.kr/streaming?device=pc&partner=pooq&pooqzone=none&region=kor&drm=wm&targetage=auto&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&contentid=K02&contenttype=live&action=hls&quality=480p&deviceModelId=Windows%2010&guid=15c20514-2ac1-11e9-a015-0eb9a3dd20c3&lastplayid=&authtype=cookie&isabr=y&ishevc=n'
    media_url = 'https://live-k02.cdn.pooq.co.kr/hls/K02/1/1000/live.m3u8?seek=0&buffer=10'
    fetcher = fetchers.hire_fetcher()
    js = json.loads(fetcher.fetch(api_url).content)
    log.debug('json ##### %s', js)
    response = fetcher.fetch(media_url, headers={'cookie': js.get('awscookie')})
    return response.content
    '''
    url = ud.Url('https://www.pooq.co.kr/player/live.html?channelid=K02')
    response = fetcher.fetch(url)
    log.debug('#### %s', response.headers)
    url = ud.Url('https://apis.pooq.co.kr/streaming?device=pc&partner=pooq&pooqzone=none&region=kor&drm=wm&targetage=auto&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&contentid=K02&contenttype=live&action=hls&quality=480p&deviceModelId=Windows%2010&guid=15c20514-2ac1-11e9-a015-0eb9a3dd20c3&lastplayid=&authtype=cookie&isabr=y&ishevc=n')
    response = fetcher.fetch(url, referer='https://www.pooq.co.kr/player/live.html?channelid=K02')
    log.debug('#### %s', response.headers)
    url = ud.Url('https://live-k02.cdn.pooq.co.kr/hls/K02/1/1000/live.m3u8?seek=0&buffer=10')
    response = fetcher.fetch(url, referer='https://www.pooq.co.kr/player/live.html?channelid=K02')
    log.debug('#### %s', response.headers)
    return response.content
    '''

'''
https://apis.pooq.co.kr/streaming?device=pc&partner=pooq&pooqzone=none&region=kor&drm=wm&targetage=auto&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&contentid=K02&contenttype=live&action=hls&quality=480p&deviceModelId=Windows%2010&guid=15c20514-2ac1-11e9-a015-0eb9a3dd20c3&lastplayid=&authtype=cookie&isabr=y&ishevc=n
device: pc
partner: pooq
pooqzone: none
region: kor
drm: wm
targetage: auto
apikey: E5F3E0D30947AA5440556471321BB6D9
credential: none
contentid: K02
contenttype: live
action: hls
quality: 480p
deviceModelId: Windows 10
guid: 15c20514-2ac1-11e9-a015-0eb9a3dd20c3
lastplayid:
authtype: cookie
isabr: y
ishevc: n

http://localhost:8081/proxy/client?source=http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8
http://qthttp.apple.com.edgesuite.net/1010qwoeiuryfg/sl.m3u8
http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8
http://devimages.apple.com/iphone/samples/bipbop/gear1/prog_index.m3u8
http://playertest.longtailvideo.com/adaptive/oceans_aes/oceans_aes.m3u8 (AES encrypted)
http://playertest.longtailvideo.com/adaptive/captions/playlist.m3u8 (HLS stream with CEA-608 captions)
http://playertest.longtailvideo.com/adaptive/wowzaid3/playlist.m3u8 (with metadata)
http://content.jwplatform.com/manifests/vM7nH0Kl.m3u8
http://cdn-fms.rbs.com.br/hls-vod/sample1_1500kbps.f4v.m3u8
http://cdn-fms.rbs.com.br/vod/hls_sample1_manifest.m3u8
http://vevoplaylist-live.hls.adaptive.level3.net/vevo/ch1/appleman.m3u8 (LIVE TV)
http://vevoplaylist-live.hls.adaptive.level3.net/vevo/ch2/appleman.m3u8 (LIVE TV)
http://vevoplaylist-live.hls.adaptive.level3.net/vevo/ch3/appleman.m3u8 (LIVE TV)
http://www.nacentapps.com/m3u8/index.m3u8 (VOD)
http://srv6.zoeweb.tv:1935/z330-live/stream/playlist.m3u8 (LIVE TV)
http://content.jwplatform.com/manifests/vM7nH0Kl.m3u8 ( link protection, video not encrypted )
http://sample.vodobox.net/skate_phantom_flex_4k/skate_phantom_flex_4k.m3u8 (4K HLS Video stream)
https://hlstests.eurofins-digitaltesting.com

https://www.pooq.co.kr/player/live.html?channelid=K02
https://live-k02.cdn.pooq.co.kr/hls/K02/1/1000/live.m3u8?seek=0&buffer=10

https://apis.pooq.co.kr/streaming?device=pc&partner=pooq&pooqzone=none&region=kor&drm=wm&targetage=auto&apikey=E5F3E0D30947AA5440556471321BB6D9&credential=none&contentid=K02&contenttype=live&action=hls&quality=480p&deviceModelId=Windows%2010&guid=15c20514-2ac1-11e9-a015-0eb9a3dd20c3&lastplayid=&authtype=cookie&isabr=y&ishevc=n
'''