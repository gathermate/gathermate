# -*- coding: utf-8 -*-

import logging

from flask import url_for
from flask import current_app as app

from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def pack_m3u(channels):
    yield '#EXTM3U\n'
    for channel in channels:
        yield '#EXTINF:-1 tvg-id="{}" tvg-logo="{}" tvh-chnum="None",{}\n' \
            .format(channel.id, channel.logo, channel.name)
        url = url_for('.streamer_channel_streaming',
                      _external=True,
                      streamer=channel.streamer.lower(),
                      cid=channel.id)
        url = ud.Url(url)
        url.username = app.config.get('AUTH_ID')
        url.password = app.config.get('AUTH_PW')
        yield url.text + '\n'
