# -*- coding: utf-8 -*-

import time
import logging
import re

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'Scraper', Tfreeca

class Tfreeca(BoardScraper):
    URL = 'https://www.tfreeca22.com/home.php'
    LIST_URL = ud.join(URL, '/board.php?mode=list&b_id=%s')
    ID_REGEXP = re.compile(r'.*id=(\d{2,7})')
    SEARCH_QUERY = 'x=0&y=0&sc=%s'
    PAGE_QUERY = 'page=%d'

    def get_list(self, r):
        tree = self.etree(r, self.encoding)

        list_xpath = r'//td[@class="subject"]/div/a[contains(@class, "stitle")]'
        for e in tree.xpath(list_xpath):
            try:
                title = e.xpath('string()').strip()
                if title == '': continue
                link = e.get('href').strip()
                id_ = self.get_id_num(link)
                # extra info
                category = e.getparent().find('a[1]/span').text
                date = e.getparent().getparent().getparent().find('td[3]').text
                etc = '{} {}'.format(category, date)
                yield {'id': id_, 'title': title, 'link': link, 'etc': etc}
            except:
                GathermateException.trace_error()

        caption_xpath = r'//td[normalize-space(@class)="subject"]//a[contains(@href, "wr_id")]/text()/..'
        for e in tree.xpath(caption_xpath):
            try:
                title = e.text.strip()
                if title == '': continue
                link = e.get('href')
                id_ = self.get_id_num(link)
                yield {'id': id_, 'title': title, 'link': link}
            except:
                GathermateException.trace_error()

    def get_item(self, r):
        tree = self.etree(r, self.encoding)

        item_xpath = r'//a[contains(@href, "filetender.com")]/text()/..'
        for e in tree.xpath(item_xpath):
            try:
                name = e.text.strip()
                link = e.get('href').strip()
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()

        url = ud.Url(r.url)
        if not url.query_dict.get('bo_table', [''])[0] == 'captions':
            iframe_xpath = r'//iframe[contains(@src, "info.php")]/@src'
            iframe_url = tree.xpath(iframe_xpath)[0]
            iframe_url = ud.join(self.URL, iframe_url)
            iframe_tree = self.fetch_and_etree(iframe_url,
                                               referer=r.url,
                                               encoding=self.encoding)

            magnet_xpath = r'//div[contains(@class, "torrent_file")]'
            for e in iframe_tree.xpath(magnet_xpath):
                try:
                    name = e.text.strip()
                    link = e.getnext()[0].get('href').strip()
                    yield {'name': name, 'link': link, 'type': 'magnet'}
                except:
                    GathermateException.trace_error()

        caption_xpath = r'//a[contains(@href, "file_download")]'
        script_regexp = re.compile(r'javascript:file_download\([\'"](.*)[\'"]\,\s[\'"](.*)[\'"]\);')
        for e in tree.xpath(caption_xpath):
            try:
                match = script_regexp.search(e.get('href'))
                name = match.group(2)
                link = ud.join(self.URL, match.group(1))
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()

    def get_file(self, url, ticket):
        key_xpath = r'//form/input[@name="key"]/@value'

        tree = self.fetch_and_etree(url,
                                    referer=ticket['referer'],
                                    encoding=self.encoding)

        key = tree.xpath(key_xpath)
        log.info("Wait for Linktender's countdown...")
        time.sleep(3)
        log.info('Start download on Linktender...')

        return self.fetch('http://file.filetender.com/Execdownload.php?link=%s' % key,
                          referer=url.text)
