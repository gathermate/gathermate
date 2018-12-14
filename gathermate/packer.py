# -*- coding: utf-8 -*-

import logging as log
import traceback

from lxml import etree
from lxml.builder import E
from flask import url_for

from util import urldealer as ud
from util import toolbox as tb

ACCEPTED_EXT = []

def get_rss_builder():
    # type: () -> lxml.etree._Element
    rss = E.rss(
        {'version': '2.0'},
        E.channel(
            E.title('My Torrent RSS'),
            E.link('https://google.com')
        )
    )
    return rss

def pack_rss(articles):
    # type (Union[List[object], Generator], Text) -> Text
    rss = get_rss_builder()

    for article in list(articles)[::-1]:
        for item in article:
            try:
                # RSS_AGGRESSIVE = False
                if item['type'] == 'unknown':
                    e_item = E.item(E.title(item['name']))
                    rss[0].append(e_item)
                    e_enclosure = E.enclosure()
                    e_item.append(e_enclosure)
                    url = url_for('.order',
                                  _external=True,
                                  order='down',
                                  url=ud.quote(item['link']))
                    e_enclosure.set('url', unicode(url))

                # RSS_AGGRESSIVE = True
                if tb.get_ext(item['name'])[1] in ACCEPTED_EXT or item['type'] in ['magnet']:
                    e_item = E.item(E.title(item['name']))
                    rss[0].append(e_item)
                    e_enclosure = E.enclosure()
                    e_item.append(e_enclosure)

                    if item['type'] == 'file':
                        url = url_for('.order',
                                      _external=True,
                                      order='down',
                                      url=ud.quote(item['link']),
                                      ticket=ud.quote(ud.unsplit_qs(item['ticket'])))
                        e_enclosure.set('url', unicode(url))
                    else:
                        e_enclosure.set('url', ud.unquote(item['link']))
                    e_enclosure.set('type', tb.get_mime(item['name']))
            except:
                log.error('\n%s', traceback.format_exc())
                log.error('Skipped item: %s', item)
    return etree.tostring(rss, pretty_print=True, xml_declaration=True, encoding='utf-8')

def pack_list(data_dict):
    # type (Dict[Text, object]) -> Dict[Text, object]
    data_dict['articles'] = sorted(data_dict['articles'].items(), reverse=True)
    return data_dict

def pack_item(items):
    # type (List[Dict[Text, object]]) -> List[Dict[Text, object]]
    for idx, item in enumerate(items):
        if item['type'] in ['magnet', 'link']:
            item['link'] = ud.unquote(item['link'])
            continue
        if not tb.get_ext(item['name'])[1] in ACCEPTED_EXT:
            log.debug(ACCEPTED_EXT)
            log.warning('%s does not have accepted extension.', item['name'])
            items.pop(idx)
            continue

        item['ticket'] = ud.quote(ud.unsplit_qs(item['ticket']))
    return items
