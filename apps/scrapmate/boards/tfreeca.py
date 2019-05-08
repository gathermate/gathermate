# -*- coding: utf-8 -*-

import time
import logging
import re
import base64
import random
import math
import json

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

        list_xpath = r'//td[@class="subject"]/div/a[2]'
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

        '''
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
        '''

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
        tree = self.fetch_and_etree(url,
                                    referer=ticket['referer'],
                                    encoding=self.encoding)
        forms = tree.xpath(r'//form[@id="Down"]')
        inputs = {}
        for form in forms:
            for inpt in form.findall('.//input'):
                inputs[inpt.get('name')] = inpt.get('value')
        payload = {
            'aid': tree.xpath(r'//a[@id="TencentCaptcha"]')[0].get('data-appid'),
            'accver': 1,
            'showtype': 'popup',
            'ua': base64.b64encode(self.fetcher.HEADERS['User-Agent']),
            'noheader': 1,
            'fb': 1,
            'fpinfo': 'fpsig=undefined',
            'grayscale': 1,
            'clienttype': 2,
            'cap_cd': '',
            'uid': '',
            'wxLang': '',
            'subsid': 1,
            'callback': '_aq_%d' % math.floor(1e6 * random.random()) ,
            'sess': '',
        }
        captcha_url = ud.Url('https://ssl.captcha.qq.com/cap_union_prehandle').update_query(payload)
        r  = self.fetch(captcha_url, referer=url.text)
        match = re.search(r'_aq_\d+\((\{.+\})\)', r.content)
        if match:
            js = json.loads(match.group(1))
            inputs['Ticket'] = js['ticket']
            inputs['Randstr'] = js['randstr']
            down_url = ud.Url('http://file.filetender.com/file.php').update_query(inputs)
            log.info("Wait for Linktender's countdown...")
            time.sleep(3)
            log.info('Start download on Linktender...')
            return self.fetch(down_url, referer=url.text)
        else:
            raise GathermateException('Failed to pass captcha.')
