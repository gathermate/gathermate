# -*- coding: utf-8 -*-

import re
import logging

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger()

def register():
    return 'Scraper', Torrentdal

class Torrentdal(BoardScraper):
    URL = 'https://torrentdal5.net/'
    LIST_URL = ud.join(URL, 'bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')
    PAGE_QUERY = 'page=%d'
    SEARCH_QUERY = 'sca=&sop=and&sfl=wr_subject&stx=%s'

    LIST_XPATH = r'//table[contains(@class, "list")]//tr/td[@class="list-subject"]/a'
    GALL_XPATH = r'//div[@class="list-item"]'
    def get_list(self, r):
        tree = self.etree(r, self.encoding)
        for a in tree.xpath(self.LIST_XPATH):
            try:
                title = a.xpath('string()')
                link = a.get('href')
                id_ = self.get_id_num(link)
                vol_td = a.getparent().getnext()
                date_td = vol_td.getnext()
                vol = vol_td.xpath('string()')
                date = date_td.xpath('string()')
                yield {'id': id_, 'title': title, 'link': link, 'etc': '{} {}'.format(vol, date)}
            except:
                GathermateException.trace_error()
        for div in tree.xpath(self.GALL_XPATH):
            try:
                a = div.find('strong/a')
                title = a.text.strip()
                link = a.get('href')
                id_ = self.get_id_num(link)
                vol = div.find('div[2]/span[1]').xpath('string()')
                date = div.find('div[2]/span[2]').xpath('string()')
                yield {'id': id_, 'title': title, 'link': link, 'etc': '{} {}'.format(vol, date)}
            except:
                GathermateException.trace_error()

    ITEM_XPATH = r'//div[contains(@class, "list-group")]/a'
    MAGNET_XPATH = r'//ul[contains(@class, "list-group")]/a'
    SIZE_REGEXP = r'\s\([0-9\.KM]+?\)$'
    def get_item(self, r):
        tree = self.etree(r, self.encoding)
        names = []
        for a in tree.xpath(self.ITEM_XPATH):
            try:
                i = a.find('i')
                name = re.sub(self.SIZE_REGEXP, '', i.tail.strip())
                link = a.get('href')
                if 'link' in i.get('class'):
                    yield {'name': name, 'link': link, 'type': 'link'}
                else:
                    yield {'name': name, 'link': link, 'type': 'file'}
                    if tb.get_ext(name)[1] == '.torrent':
                        names.append(name)
            except:
                GathermateException.trace_error()
        for idx, a in enumerate(tree.xpath(self.MAGNET_XPATH)):
            try:
                if idx < len(names):
                    yield {'name': names[idx], 'link': a.get('href'), 'type': 'magnet'}
            except:
                GathermateException.trace_error()

    def get_file(self, url, ticket):
        return self.fetch(url, referer=ticket['referer'])






