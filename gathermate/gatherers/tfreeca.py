# -*- coding: utf-8 -*-

import time
import logging as log
import re

from gathermate.gatherer import Gatherer
from util import urldealer as ud

def register():
    return 'Gatherer'

class Tfreeca(Gatherer):
    URL = 'http://www.tfreeca22.com/main.php'
    LIST_URL = ud.join(URL, '/board.php?mode=list&b_id=%s')
    ID_REGEXP = re.compile(r'.*id=(\d{2,7})')
    SEARCH_QUERY = 'x=0&y=0&sc=%s'
    PAGE_QUERY = 'page=%d'

    list_xpath = r'//td[normalize-space(@class)="subject"]//a[contains(@href, "mode=view")]'
    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        tree = self.etree(r, self.encoding)
        for e in tree.xpath(self.list_xpath):
            try:
                title = e.xpath('string()').strip()
                link = e.get('href').strip()
                id_ = self.get_id_num(link)
                yield {'id': id_, 'title': title, 'link': link}
            except:
                self.trace_error()

    item_xpath = r'//a[contains(@href, "filetender.com")]/text()/..'
    iframe_xpath = r'//iframe[contains(@src, "info.php")]/@src'
    magnet_xpath = r'//div[contains(@class, "torrent_file")]'
    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        tree = self.etree(r, self.encoding)

        for e in tree.xpath(self.item_xpath):
            try:
                name = e.text.strip()
                link = e.get('href').strip()
                link_type = self.is_magnet(link)
                yield {'name': name, 'link': link, 'type': link_type}
            except:
                self.trace_error()


        iframe_url = self.etree(r, encoding=self.encoding).xpath(self.iframe_xpath)[0]
        iframe_url = ud.join(self.URL, iframe_url)
        iframe_tree = self.fetch_and_etree(iframe_url,
                                           referer=r.url,
                                           encoding=self.encoding)

        for e in iframe_tree.xpath(self.magnet_xpath):
            try:
                name = e.text.strip()
                link = e.getnext()[0].get('href').strip()
                link_type = self.is_magnet(link)
                yield {'name': name, 'link': link, 'type': link_type}
            except:
                self.trace_error()

    key_xpath = r'//form/input[@name="key"]/@value'
    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response

        tree = self.fetch_and_etree(url,
                                    referer=ticket['referer'],
                                    encoding=self.encoding)

        key = tree.xpath(self.key_xpath)
        log.info("Wait for Linktender's countdown...")
        time.sleep(3)
        log.info('Start download on Linktender...')

        return self.fetch('http://file.filetender.com/down.php?link=%s' % key,
                          referer=url.text)
