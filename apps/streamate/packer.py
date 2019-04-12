# -*- coding: utf-8 -*-

import logging

from flask import url_for
from flask import current_app as app
from lxml import etree
from lxml.builder import E

from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def channels_by_streamer(streamer_name, mapped_channels):
    channels = {}
    for cid, ch in mapped_channels.iteritems():
        if ch.get(streamer_name) is not None:
            ch['cid'] = cid
            channels[str(ch.get(streamer_name))] = ch
    return channels

def pack_m3u(streamer, mapped_channels, ffmpeg):
    '''
    - tvg-id is value of '<channel id="">' in EPG xml file. If the tag is absent then addon will use tvg-name for map channel to EPG;
    - tvg-name is value of display-name in EPG there all space chars replaced to _ (underscore char) if this value is not found in xml then addon will use the channel name to find correct EPG.
    - tvg-logo is name of channel logo file. If this tag is absent then addon will use channel name to find logo.
    - tvg-shift is value in hours to shift EPG time. This tag can be used in #EXTM3U for apply shift to all channels or in #EXTINF for apply shift only to current channel.
    - group-name is channels group name. If the tag is absent then addon will use group name from the previous channel.
    '''
    yield '#EXTM3U\n'
    streamer_name = streamer.__class__.__name__.lower()
    for channel in streamer.get_channels():
        yield '#EXTINF:-1 tvg-id="{cid}" tvg-logo="{logo}" tvh-chnum="{chnum}" group-name="{streamer}",{name}\n' \
            .format(streamer=channel.streamer.lower(),
                    cid=channel.getlist('cid')[-1] if len(channel.getlist('cid')) > 1 else '%s.%s' % (channel.cid, streamer_name),
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
            cmd = app.config.get('STREAMATE', {}).get('FFMPEG_COMMAND', 'pipe://{ffmpeg} -i {url} -c copy -f mpegts pipe:1')
            yield cmd.format(ffmpeg=ffmpeg, url=url.text) + '\n'
        else:
            yield url.text + '\n'

def pack_channels(streamer, mapped_channels):
    streamer_name = streamer.__class__.__name__.lower()
    registered_channels = channels_by_streamer(streamer_name, mapped_channels)
    info = "'{cid}':dict(name='{name}',chnum={chnum},{streamer}={scid},{extra}logo='{logo}'),\n"
    yield '{\n'
    for ch in streamer.get_channels():
        scid = ch.cid
        if ch.cid in registered_channels:
            for k, v in registered_channels[str(ch.cid)].iteritems():
                if k == 'name' or k == 'logo' or k == streamer_name:
                    continue
                ch[k] = v
            yield info.format(cid=ch.pop('cid'),
                              name=ch.pop('name'),
                              chnum=ch.pop('chnum'),
                              streamer=ch.pop('streamer').lower(),
                              scid=scid if str(scid).isdigit() else "'%s'" % scid,
                              logo=ch.pop('logo'),
                              extra=','.join("%s=%s" % (k, v[0] if str(v[0]).isdigit() else "'%s'" % v[0]) for k, v in ch.iteritems()) + ','
                              )
        else:
            yield info.format(cid='%s.%s' % (scid, streamer_name),
                              name=ch.name,
                              chnum=ch.pop('chnum'),
                              streamer=ch.streamer.lower(),
                              scid=scid if str(scid).isdigit() else "'%s'" % scid,
                              logo=ch.logo,
                              extra="only='%s'," % streamer_name)
    yield '}\n'



LANG = {'lang':'kr'}
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
                program = E.programme(
                    {
                        'start': p.starts,
                        'stop': p.stops,
                        'channel': cid,
                    },
                    E.title(LANG, p['title'] + ' (재)' if p.rerun else p['title'])
                )
                if p.cid:
                    program.set('source-channel', unicode(p.cid))
                if p.sub_title:
                    sub_title = etree.SubElement(program, 'sub-title')
                    sub_title.set('lang', 'kr')
                    sub_title.text = p.sub_title
                if p.description:
                    program.append(E.desc(LANG, p.description))
                if p.getlist('category'):
                    for c in p.getlist('category'):
                        if c is not None: program.append(E.category(LANG, c))
                if p.rating:
                    program.append(E.rating(str(p.rating)))
                yield etree.tostring(program,
                                     encoding='utf-8',
                                     pretty_print=True)
    yield '</tv>'
