# -*- coding: utf-8 -*-
import time
import logging
import re

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import MyFlaskException
from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def register():
    return 'Scraper', Torrentzoa


class Torrentzoa(BoardScraper):
    URL = "https://www.torrentzoa.com/"
    LIST_URL = ud.join(URL, 'torrent-%s-p1.html')
    SEARCH_QUERY = 'search-%s-%s-p1.html'
    PAGE_QUERY = 'p%d.html'
    ID_REGEXP = re.compile(r'(\d{2,8})\.html')

    def handle_search(self, url, keyword):
        path_split = url.path.split('-')
        url.path = self.SEARCH_QUERY % (path_split[1], keyword)

    def handle_page(self, url, num):
        path_split = url.path.split('-')
        path_split[2] = self.PAGE_QUERY % int(num)
        url.path = '-'.join(path_split)

    def get_list(self, r):
        root = self.etree(r, encoding=self.encoding)

        list_xpath = r'//table/tbody/tr//a[2]'
        for e in root.xpath(list_xpath):
            try:
                link = e.get('href')
                title = e.xpath('string()').strip()
                id_ = self.get_id_num(link)
                date = e.getparent().getparent().getparent().find('td[3]').text
                category = e.getparent().find('a[1]').text
                etc = '{} {}'.format(category, date)
                yield {'id': id_, 'title': title, 'link': link, 'etc': etc}
            except:
                MyFlaskException.trace_error()

    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)

        item_xpath = r'//a[contains(@href, "filetender")]'
        for e in root.xpath(item_xpath):
            try:
                name = e.text.strip()
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                MyFlaskException.trace_error()

    def get_file(self, url, ticket):
        root = self.fetch_and_etree(url,
                                    referer=ticket['referer'],
                                    encoding='utf-8')

        key_xpath = r'//form/input[@name="key"]/@value'
        key = root.xpath(key_xpath)
        log.info("Wait for Linktender's countdown...")
        time.sleep(3)
        log.info('Start download on Linktender...')

        return self.fetch('http://file.filetender.com/Execdownload.php?link=%s' % key,
                          referer=url.text)
