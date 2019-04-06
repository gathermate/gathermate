# -*- coding: utf-8 -*-
import re
import logging

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import MyFlaskException
from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def register():
    return 'Scraper', Boza

class Boza(BoardScraper):
    URL = 'https://torrentboza.net/'
    LIST_URL = ud.join(URL, '/bbs/board.php?bo_table=%s')
    SEARCH_QUERY = 'sca=&sfl=wr_subject&sop=and&stx=%s'
    PAGE_QUERY = 'page=%d'
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')

    def get_list(self, r):
        root = self.etree(r, encoding=self.encoding)

        list_xpath = r'//ul[@class="list-body"]/li/div/a'
        for e in root.xpath(list_xpath):
            try:
                link = e.get('href')
                title = e.xpath('string()')
                id_ = self.get_id_num(link)
                date = e.getparent().xpath('div/span[2]')[0].xpath('string()')
                yield {'id': id_, 'title': title, 'link': link, 'etc': date}
            except:
                MyFlaskException.trace_error()

    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)

        title_regexp = re.compile(r'\s\(\d+.*\)$')
        item_xpath = r'//a[contains(@class, "list-group-item") and contains(@href, "http")]'
        for e in root.xpath(item_xpath):
            try:
                name = title_regexp.sub('', e.find('i[@class="fa fa-download"]').tail.strip())
                link = e.get('href')
                yield {'name': name.decode('utf-8', 'ignore'), 'link': link, 'type': 'file'}
            except:
                MyFlaskException.trace_error()

        magnet_xpath = r'//a[contains(@href, "magnet:?xt=")]'
        for e in root.xpath(magnet_xpath):
            try:
                name = e.getparent().getparent().xpath('div/h3/i')[0].tail.strip()
                name = title_regexp.sub('', name)
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'magnet'}
            except:
                MyFlaskException.trace_error()

    def get_file(self, url, ticket):
        if self.aggressive:
            self.fetch(ud.Url(ticket['referer']), referer=self.URL)
        return self.fetch(url, referer=ticket['referer'])
