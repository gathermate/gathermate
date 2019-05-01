# -*- coding: utf-8 -*-
import time
import logging
import re

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'Scraper', Torrentmi


class Torrentmi(BoardScraper):
    URL = "https://www.torrentmi.com"
    LIST_URL = ud.join(URL, '/list.php?b_id=%s')
    SEARCH_QUERY = 'sc=%s'
    PAGE_QUERY = 'page=%d'
    ID_REGEXP = re.compile(r'id=(\d{2,8})')

    def get_list(self, r):
        root = self.etree(r, encoding=self.encoding)

        list_xpath = r'//div[@class="sub_list"]/div/table/tbody/tr/td[2]/a'
        for e in root.xpath(list_xpath):
            try:
                link = e.get('href')
                title = e.find('span[1]').xpath('string()').strip()
                id_ = self.get_id_num(link)
                date = e.getparent().getparent().find('td[3]').text
                category = e.find('em').text
                etc = '{} {}'.format(category, date)
                yield {'id': id_, 'title': title, 'link': link, 'etc': etc}
            except:
                GathermateException.trace_error()

    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)

        item_xpath = r'//div[@class="downLoad"]/a[1]'
        for e in root.xpath(item_xpath):
            try:
                name = e.text.strip()
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()

    def get_file(self, url, ticket):
        root = self.fetch_and_etree(url,
                                    referer=ticket['referer'],
                                    encoding='utf-8')

        key_xpath = r'//form/input[@name="key"]/@value'
        key = root.xpath(key_xpath)
        log.info("Wait for Linktender's countdown...")
        time.sleep(3)
        log.info('Start download on Linktender...')

        return self.fetch(u'http://file.filetender.com/down.php?link=%s' % key,
                          referer=url.text)
