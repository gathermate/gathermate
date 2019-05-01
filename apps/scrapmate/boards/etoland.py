# -*- coding: utf-8 -*-
import re
import logging

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'Scraper', Etoland


class Etoland(BoardScraper):
    URL = "http://www.etoland.co.kr"
    LIST_URL = ud.join(URL, '/bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')
    SEARCH_QUERY = 'sca=&sfl=wr_subject&stx=%s&x=0&y=0'
    PAGE_QUERY = 'page=%d'

    def set_login(self, login_info):
        self.login_info = {
            'payload': {
                'mb_id': login_info.get('mb_id'),
                'mb_password': login_info.get('mb_password'),
                'url': 'http://www.etoland.co.kr',
                'auto_login': 1,
                'x': 0,
                'y': 0,
            },
            'url': 'https://www.etoland.co.kr/bbs/login_check2.php',
            'denied': re.compile('alert\([\'"].+권한.+[\'"]\);'.encode(self.encoding)),
        }

    def handle_search(self, url, keyword):
        url.update_qs(self.SEARCH_QUERY % keyword.encode(self.encoding))

    def get_list(self, r):
        list_xpath = r'//td[contains(@class, "mw_basic_list_subject")]/a/span[not(@class)]/..'
        for e in self.etree(r, encoding=self.encoding).xpath(list_xpath):
            try:
                title = e.xpath('string()')
                link = e.get('href').strip()
                id_ = self.get_id_num(link)
                date = e.getparent().getparent().findall('td')[3].text
                catext = e.getparent().find('a[1]').text
                if catext:
                    etc = '{} {}'.format(catext.strip(), date)
                else:
                    etc = date
                yield {'id': id_, 'title': title, 'link': link, 'etc': etc}
            except:
                GathermateException.trace_error()

    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)

        item_xpath = r'//td[@class="mw_basic_view_file"]/a[contains(@onclick, "file_download")]'
        onclick_regexp = re.compile(r'file_download\(\'\.(.*)\',\s\'(.*)\',\s\'(.*)\'\);')
        for e in root.xpath(item_xpath):
            try:
                matches = onclick_regexp.search(e.get('onclick'))
                name = matches.group(2)
                link = 'http://www.etoland.co.kr/bbs{}'.format(matches.group(1))
                yield {'name': name, 'link': link, 'type': 'file', 'etc': 'test'}
            except:
                GathermateException.trace_error()

        for e in root.xpath(r'//td[@class="mw_basic_view_file"]/a[contains(@href, "magnet")]'):
            try:
                name = e.getparent().getparent().getparent().xpath('tr/td[@class="mw_basic_view_subject"]/h1')[0].text.strip()
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'magnet'}
            except:
                GathermateException.trace_error()

        location_regexp = re.compile(r'location\.replace\(["\'](.+)["\']\);')
        for e in root.xpath(r'//td[@class="mw_basic_view_link"]/a'):
            try:
                name = e.text.strip()
                if name.endswith('…'):
                    link = ud.join('%s/dummy/' % self.URL, e.get('href'))
                    link_r = self.fetch(link, referer=r.url)
                    match = location_regexp.search(link_r.content)
                    if match:
                        name = match.group(1)
                yield {'name': name, 'link': name, 'type': 'link'}
            except:
                GathermateException.trace_error()

        url = ud.Url(r.url)
        if url.query_dict.get('bo_table').startswith('data_'):
            elements = root.xpath(r'//a[contains(@href, "https://www.google.com")]/font/..')
            for e in elements:
                try:
                    link = e.get('href')
                    yield {'name': link, 'link': link, 'type': 'link'}
                except:
                    GathermateException.trace_error()

    def get_file(self, url, ticket):
        return self.fetch(url, referer=ticket['referer'])
