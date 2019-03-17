# -*- coding: utf-8 -*-

import logging

from flask import url_for
from flask import current_app as app
from lxml import etree
from lxml.builder import E

from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def pack_m3u(channels):
    yield '#EXTM3U\n'
    for channel in channels:
        yield '#EXTINF:-1 tvg-id="{cid}.{streamer}" tvg-logo="{logo}" tvh-chnum="None",{name}\n' \
            .format(streamer=channel.streamer.lower(),
                    cid=channel.id,
                    logo=channel.logo,
                    name=channel.name)
        url = url_for('.streamer_channel_streaming',
                      _external=True,
                      streamer=channel.streamer.lower(),
                      cid=channel.id)
        url = ud.Url(url)
        url.username = app.config.get('AUTH_ID')
        url.password = app.config.get('AUTH_PW')
        yield url.text + '\n'

def pack_epg(channel_generator):
    '''
    Change it to generator!
    '''
    yield '''<?xml version="1.0" encoding="UTF-8"?>
<tv generator-info-name="Gathermate">\n'''
    for ch in channel_generator:
        cid = '{}.{}'.format(ch.cid, ch.streamer)
        channel = E.channel({'id': cid})
        dp_name = etree.SubElement(channel, 'display-name')
        dp_name.text = unicode(ch.getlist('name')[-1])
        yield etree.tostring(channel,
                             encoding='utf-8',
                             pretty_print=True)
        if ch.epg is None or ch.epg.get('programs') is None:
            continue
        for p in ch.epg.get('programs'):
            program = E.programme({'start': p.get('start'), 'stop': p.get('stop'), 'channel': cid},
                                  E.title({'lang': 'kr'}, p.get('title'))
            )
            yield etree.tostring(program,
                                 encoding='utf-8',
                                 pretty_print=True)
    yield '</tv>'
