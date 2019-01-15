# -*- coding: utf-8 -*-
import time
import logging as log
import re

from gathermate.gatherer import Gatherer
from gathermate.exception import GathermateException as GE
from util import urldealer as ud

def register():
    return 'Gatherer'


class Torrentmi(Gatherer):
    URL = "https://www.torrentmi.com"
    LIST_URL = ud.join(URL, '/list.php?b_id=%s')
    SEARCH_QUERY = 'sc=%s'
    PAGE_QUERY = 'page=%d'
    ID_REGEXP = re.compile(r'id=(\d{2,8})')

    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
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
                GE.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        root = self.etree(r, encoding=self.encoding)

        item_xpath = r'//div[@class="downLoad"]/a[1]'
        for e in root.xpath(item_xpath):
            try:
                name = e.text.strip()
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GE.trace_error()
        '''
        iframe_xpath = r'//iframe[contains(@src, "info.php")]/@src'
        magnet_xpath = r'//div[contains(@class, "torrent_file")]'
        iframe_url = self.etree(r, encoding=self.encoding).xpath(iframe_xpath)[0]
        root = self.fetch_and_etree(iframe_url,
                                    referer=r.url,
                                    encoding=self.encoding).xpath(magnet_xpath)
        for e in root:
            try:
                name = e.text.strip()
                link = e.getnext()[0].get('href').strip()
                yield {'name': name, 'link': link, 'type': 'magnet'}
            except:
                GE.trace_error()
        '''

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response
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
