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

    def __init__(self, settings, fetcher):
        HlsStreamer.__init__(self, settings, fetcher)



#for testing
import app
from apps.common import fetchers

if __name__ == '__main__':
    app = app.app
    print app.config['STREAMATE']
    print 'test'
    ok = Oksusu(app.config.get('STREAMATE'))