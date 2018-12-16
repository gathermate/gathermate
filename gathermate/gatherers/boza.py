# -*- coding: utf-8 -*-

import re
import logging as log

from lxml import etree

from gathermate.gatherer import Gatherer
from util import urldealer as ud

def register():
    return 'Gatherer'

class Boza(Gatherer):
    URL = 'https://torrentboza.com/'
    LIST_URL = ud.join(URL, '/bbs/board.php?bo_table=%s')
    SEARCH_QUERY = 'sca=&sfl=wr_subject&sop=and&stx=%s'
    PAGE_QUERY = 'page=%d'
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')

    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        list_xpath = r'//ul[@class="list-body"]//li[@class="list-item"]//a[@class="item-subject"]'
        root = self.etree(r, encoding=self.encoding)
        for e in root.xpath(list_xpath):
            try:
                link = e.get('href')
                title = e.xpath('string()')
                id_ = self.get_id_num(link)
                yield {'id': id_, 'title': title, 'link': link}
            except:
                self.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        item_xpath = r'//a[contains(@class, "list-group-item") and contains(@href, "http")]'
        magnet_xpath = r'//a[contains(@href, "magnet:?xt=")]'
        title_regexp = re.compile(r'\s\(\d+.*\)$')
        root = self.etree(r, encoding=self.encoding)
        for e in root.xpath(item_xpath):
            try:
                name = title_regexp.sub('', e.find('i[@class="fa fa-download"]').tail.strip())
                link = e.get('href')
                yield {'name': name.decode('utf-8', 'ignore'), 'link': link, 'type': self.is_magnet(link)}
            except:
                self.trace_error()

        for e in root.xpath(magnet_xpath):
            try:
                name = e.getparent().getparent().xpath('div/h3/i')[0].tail.strip()
                name = title_regexp.sub('', name)
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'magnet'}
            except:
                self.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response
        return self.fetch(url, referer=ticket['referer'])
