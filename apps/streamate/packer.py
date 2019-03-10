# -*- coding: utf-8 -*-

import logging

from flask import url_for

log = logging.getLogger(__name__)

def pack_m3u(channels):
    yield '#EXTM3U\n'
    for channel in channels:
        yield '#EXTINF:-1 tvg-id="{}" tvg-logo="None" tvh-chnum="None",{}\n'.format(channel.id, channel.name)
        url = url_for('.streamer_channel_streaming',
                      _external=True,
                      streamer=channel.streamer.lower(),
                      cid=channel.id)
        yield url + '\n'
