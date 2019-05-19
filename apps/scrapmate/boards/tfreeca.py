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

    LIST_XPATH = r'//td[@class="subject"]/div/a[2]'
    CAPTION_XPATH = r'//td[normalize-space(@class)="subject"]//a[contains(@href, "wr_id")]/text()/..'
    def get_list(self, r):
        tree = self.etree(r, self.encoding)
        for e in tree.xpath(self.LIST_XPATH):
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
        for e in tree.xpath(self.CAPTION_XPATH):
            try:
                title = e.text.strip()
                if title == '': continue
                link = e.get('href')
                id_ = self.get_id_num(link)
                yield {'id': id_, 'title': title, 'link': link}
            except:
                GathermateException.trace_error()

    ITEM_XPATH = r'//a[contains(@href, "filetender.com")]/text()/..'
    MAGNET_IFRAME_XPATH = r'//iframe[contains(@src, "info.php")]/@src'
    MAGNET_XPATH = r'//div[contains(@class, "torrent_file")]'
    CAPTION_XPATH = r'//a[contains(@href, "file_download")]'
    SCRIPT_REGEXP = re.compile(r'javascript:file_download\([\'"](.*)[\'"]\,\s[\'"](.*)[\'"]\);')
    def get_item(self, r):
        tree = self.etree(r, self.encoding)
        for e in tree.xpath(self.ITEM_XPATH):
            try:
                name = e.text.strip()
                link = e.get('href').strip()
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()
        # Magnet handling
        url = ud.Url(r.url)
        if not url.query_dict.get('bo_table', [''])[0] == 'captions':
            iframe_url = tree.xpath(self.MAGNET_IFRAME_XPATH)[0]
            iframe_url = ud.join(self.URL, iframe_url)
            iframe_tree = self.fetch_and_etree(iframe_url,
                                               referer=r.url,
                                               encoding=self.encoding)
            for e in iframe_tree.xpath(self.MAGNET_XPATH):
                try:
                    name = e.text.strip()
                    link = e.getnext()[0].get('href').strip()
                    yield {'name': name, 'link': link, 'type': 'magnet'}
                except:
                    GathermateException.trace_error()
        # Caption board handling
        for e in tree.xpath(self.CAPTION_XPATH):
            try:
                match = self.SCRIPT_REGEXP.search(e.get('href'))
                name = match.group(2)
                link = ud.join(self.URL, match.group(1))
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()

    FORM_XPATH = r'//form[@id="Down"]'
    CAPTCHA_XPATH = r'//a[@id="TencentCaptcha"]'
    def get_file(self, url, ticket):
        tree = self.fetch_and_etree(url,
                                    referer=ticket['referer'],
                                    encoding=self.encoding)
        forms = tree.xpath(self.FORM_XPATH)
        inputs = {inpt.get('name'): inpt.get('value') for form in forms for inpt in form.findall('.//input')}
        '''
        # If captcha exists...
        payload = {
            'aid': tree.xpath(self.CAPTCHA_XPATH)[0].get('data-appid'),
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
        else:
            raise GathermateException('Failed to pass captcha.')
        '''
        down_url = ud.Url('http://file.filetender.com/file.php').update_query(inputs)
        log.info("Wait for Linktender's countdown...")
        time.sleep(3)
        log.info('Start download on Linktender...')
        return self.fetch(down_url, referer=url.text)

