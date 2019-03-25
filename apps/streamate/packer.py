# -*- coding: utf-8 -*-

import logging

from flask import url_for
from flask import current_app as app
from lxml import etree
from lxml.builder import E

from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def pack_m3u(channels, ffmpeg):
    '''
    - tvg-id is value of '<channel id="">' in EPG xml file. If the tag is absent then addon will use tvg-name for map channel to EPG;
    - tvg-name is value of display-name in EPG there all space chars replaced to _ (underscore char) if this value is not found in xml then addon will use the channel name to find correct EPG.
    - tvg-logo is name of channel logo file. If this tag is absent then addon will use channel name to find logo.
    - tvg-shift is value in hours to shift EPG time. This tag can be used in #EXTM3U for apply shift to all channels or in #EXTINF for apply shift only to current channel.
    - group-name is channels group name. If the tag is absent then addon will use group name from the previous channel.
    '''
    yield '#EXTM3U\n'
    for channel in channels:
        yield '#EXTINF:-1 tvg-id="{cid}" tvg-logo="{logo}" tvh-chnum="{chnum}" tvh-network="{streamer}",{name}\n' \
            .format(streamer=channel.streamer.lower(),
                    cid=channel.getlist('cid')[-1],
                    logo=channel.logo,
                    name=channel.name,
                    chnum=channel.chnum)
        url = url_for('.streamer_channel_streaming',
                      _external=True,
                      streamer=channel.streamer.lower(),
                      cid=channel.cid)
        url = ud.Url(url)
        url.username = app.config.get('AUTH_ID')
        url.password = app.config.get('AUTH_PW')
        if ffmpeg:
            yield 'pipe://{} -i {} -c copy -f mpegts pipe:1\n'.format(ffmpeg, url.text)
        else:
            yield url.text + '\n'

def pack_epg(channel_generator):
    yield '''<?xml version="1.0" encoding="UTF-8"?>
<tv generator-info-name="Gathermate">\n'''
    for ch in channel_generator:
        cid = ch.get('cid')
        channel = E.channel({'id': cid})
        dp_name = etree.SubElement(channel, 'display-name')
        dp_name.text = unicode(ch.get('name'))
        icon = etree.SubElement(channel, 'icon')
        icon.set('src', ch.get('logo'))
        epg = ch.get('epg')
        if epg.get('source'):
            channel.set('source-info-name', epg.get('source'))
        if epg.get('fails'):
            channel.set('fails', ', '.join(epg.get('fails')))
        yield etree.tostring(channel,
                             encoding='utf-8',
                             pretty_print=True)
        if epg.get('programs') is not None:
            for p in epg.get('programs'):
                program = E.programme({'start': p.get('start'), 'stop': p.get('stop'), 'channel': cid},
                                      E.title({'lang': 'kr'}, p.get('title'))
                )
                yield etree.tostring(program,
                                     encoding='utf-8',
                                     pretty_print=True)
    yield '</tv>'
