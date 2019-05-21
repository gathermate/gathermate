# -*- coding: utf-8 -*-

import re
import logging

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger()

def register():
    return 'Scraper', Torrentken

class Torrentken(BoardScraper):
    URL = 'https://torrentken.net/'
    LIST_URL = ud.join(URL, 'bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')
    PAGE_QUERY = 'page=%d'
    SEARCH_QUERY = 'sca=&sop=and&sfl=wr_subject%7C%7Cwr_content&stx=%s'

    LIST_XPATH = r'//table//td[@class="td_subject"]/..'
    def get_list(self, r):
        tree = self.etree(r, self.encoding)
        for tr in tree.xpath(self.LIST_XPATH):
            try:
                td_subject = tr.find('td[@class="td_subject"]')
                a = td_subject.find('div/a')
                title = a.xpath('string()')
                link = a.get('href')
                id_ = self.get_id_num(link)
                vol = tr.find('td[@class="td_size"]').text.strip()
                yield {'id': id_, 'title': title, 'link': link, 'etc': vol}
            except:
                GathermateException.trace_error()

    ITEM_XPATH = r'//section[@id="bo_v_file"]//a'
    LINK_XPATH = r'//section[@id="bo_v_atc"]//section[@id="bo_v_link"][1]//a'
    ARTICLE_TITLE = r'//span[@class="bo_v_tit"]'
    def get_item(self, r):
        tree = self.etree(r, self.encoding)
        for a in tree.xpath(self.ITEM_XPATH):
            try:
                name = a.find('strong').text.strip()
                link = a.get('href')
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()
        article_title = tree.xpath(self.ARTICLE_TITLE)[0].text.strip()
        for a in tree.xpath(self.LINK_XPATH):
            try:
                link = a.get('href')
                td = a.getparent().getparent().getprevious().find('td[2]')
                if td:
                    name = td.text
                else:
                    name = article_title
                yield {'name': name, 'link': link, 'type': 'magnet' if link.startswith('magnet') else 'link'}
            except:
                GathermateException.trace_error()

    def get_file(self, url, ticket):
        return self.fetch(url, referer=ticket['referer'])
