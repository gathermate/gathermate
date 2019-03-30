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
    return 'Streamer', Oksusu


class Oksusu(HlsStreamer):
    BASE_URL = 'https://www.oksusu.com'
    LOGIN_CHECK_URL = 'http://www.oksusu.com/my'

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
            pass

    def should_login(self):
        pass



#for testing
import app
from apps.common import fetchers

if __name__ == '__main__':
    TEST_CHANNELS = [
        dict(cid='KBS1',name='KBS 1',chnum=9,sk='5100.11',epgcokr=9,kt=9,lg=501,sky=796,pooq='K01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/9.png'),
        dict(cid='KBS2',name='KBS 2',chnum=7,sk='5100.12',epgcokr=7,kt=7,lg=502,sky=795,pooq='K02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/7.png'),
    ]
    app = app.app
    fetcher = fetchers.hire_fetcher()
    ok = Oksusu(fetcher,
                TEST_CHANNELS,
                {k.lower(): v for k, v in app.config['STREAMATE']['STREAMERS']['Oksusu'].iteritems()})
    #r = fetcher.fetch('https://www.oksusu.com/user/tid/login?rw=/')
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 10 Build/MOB31T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
    }
    r = fetcher.fetch('http://www.oksusu.com/my', headers=headers, follow_redirects=False)
    print r.content

    print r.headers