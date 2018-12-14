# -*- coding: utf-8 -*-

import re
import logging as log

from lxml import etree

from gathermate.gatherer import Gatherer
from util import urldealer as ud

def register():
    return 'Gatherer'

class Etoland(Gatherer):
    URL = "http://www.etoland.co.kr"
    LIST_URL = ud.join(URL, '/bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')
    SEARCH_QUERY = 'sca=&sfl=wr_subject&stx=%s&x=0&y=0'
    PAGE_QUERY = 'page=%d'

    def set_login(self, config):
        self.login_info = {
            'fields': {
                'mb_id': config.get('mb_id'),
                'mb_password': config.get('mb_password'),
                'url': 'http://www.etoland.co.kr',
                'auto_login': 1,
                'x': 0,
                'y': 0,
            },
            'url': 'https://www.etoland.co.kr/bbs/login_check2.php',
            'done': r'location\.replace\(\'.*\'\)\;',
            'denied': r'<script language=[\'"]javascript[\'"]>alert\(\'.*?\'\);<\/script>'
        }

    def handle_search(self, url, keyword):
        url.update_qs(self.SEARCH_QUERY % keyword.encode(self.encoding))

    list_xpath = r'//td[contains(@class, "mw_basic_list_subject")]/a/span[not(@class)]/..'
    def get_list(self, r):
        for e in self.etree(r, encoding=self.encoding).xpath(self.list_xpath):
            try:
                title = e.xpath('string()')
                link = e.get('href').strip()
                id_ = self.get_id_num(link)
                date = e.getparent().getparent().findall('td')[3].text
                yield {'id': id_, 'title': title, 'link': link, 'date': date}
            except:
                self.trace_error()

    item_xpath = r'//td[@class="mw_basic_view_file"]/a[contains(@onclick, "file_download")]'
    onclick_regexp = re.compile(r'file_download\(\'\.(.*)\',\s\'(.*)\',\s\'(.*)\'\);')
    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)
        for e in root.xpath(self.item_xpath):
            try:
                matches = self.onclick_regexp.search(e.get('onclick'))
                name = matches.group(2)
                link = 'http://www.etoland.co.kr/bbs{}'.format(matches.group(1))
                link_type = self.is_magnet(link)
                yield {'name': name, 'link': link, 'type': link_type, 'extra': 'etoeto'}
            except:
                self.trace_error()

        for e in root.xpath(r'//a[contains(@href, "magnet")]'):
            try:
                name = e.getparent().getparent().getparent().xpath('tr/td[@class="mw_basic_view_subject"]/h1')[0].text.strip()
                link = e.get('href')
                link_type = self.is_magnet(link)
                yield {'name': name, 'link': link, 'type': link_type}
            except:
                self.trace_error()

        for e in root.xpath(r'//td[@class="mw_basic_view_link"]/a'):
            try:
                name = e.text.strip()
                link = name
                link_type = 'link'
                yield {'name': name, 'link': link, 'type': link_type}
            except:
                self.trace_error()

    def get_file(self, url, ticket):
        return self.fetch(url, referer=ticket['referer'])
