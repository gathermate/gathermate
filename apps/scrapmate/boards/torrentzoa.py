# -*- coding: utf-8 -*-
import logging
import re

from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud
from apps.scrapmate.boards.tfreeca import Tfreeca

log = logging.getLogger()

def register():
    return 'Scraper', Torrentzoa


class Torrentzoa(Tfreeca):
    URL = "https://www.torrentzoa23.com/"
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
                GathermateException.trace_error()

    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)

        item_xpath = r'//a[contains(@href, "filetender")]'
        for e in root.xpath(item_xpath):
            try:
                name = e.text.strip()
                link = e.get('href')
                yield {'name': name, 'link': link, 'type': 'file'}
            except:
                GathermateException.trace_error()
