# -*- coding: utf-8 -*-

import re
import logging

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger()

def register():
    return 'Scraper', Trtcall

class Trtcall(BoardScraper):
    URL = 'https://trtcall1.com/'
    LIST_URL = ud.join(URL, 'bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')
    PAGE_QUERY = 'page=%d'
    SEARCH_QUERY = 'sca=&sfl=wr_subject&sop=and&stx=%s'

    def __init__(self, *args, **kwargs):
        BoardScraper.__init__(self, *args, **kwargs)
        self.fetcher.HEADERS['accept-language'] = 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'

    LIST_XPATH = r'//li[@class="list-item"]/div[@class="wr-subject"]/a'
    def get_list(self, r):
        tree = self.etree(r, self.encoding)
        for a in tree.xpath(self.LIST_XPATH):
            try:
                title = a.xpath('string()').strip()
                link = a.get('href')
                id_ = self.get_id_num(link)
                date = a.getparent().getnext().text.strip()
                yield {'id': id_, 'title': title, 'link': link, 'etc': date}
            except:
                GathermateException.trace_error()

    ITEM_XPATH = r'//a[contains(@class, "list-group-item")]'
    MAGNET_XPATH = r'//ul[@class="list-group"]/li/a[contains(@href, "magnet")]'
    SIZE_REGEXP = r'\s\([0-9\.KM]+?\)$'
    def get_item(self, r):
        tree = self.etree(r, self.encoding)
        '''
        for a in tree.xpath(self.ITEM_XPATH):
            try:
                if not a.get('href'):
                    continue
                link = a.get('href')
                name = re.sub(self.SIZE_REGEXP, '', a.find('i').tail.strip())
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()
        '''
        for a in tree.xpath(self.MAGNET_XPATH):
            try:
                name = a.getparent().getparent().getparent().find('div/h3/i').tail
                yield {'name': name, 'link': a.get('href'), 'type': 'magnet'}
            except:
                GathermateException.trace_error()

    def get_file(self, url, ticket):
        return self.fetch(url, referer=ticket['referer'])






