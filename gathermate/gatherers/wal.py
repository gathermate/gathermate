# -*- coding: utf-8 -*-
import re

from gathermate.gatherer import Gatherer
from util import urldealer as ud

def register():
    return 'Gatherer'


class Wal(Gatherer):
    URL = 'https://m.torrentwal.net/'
    LIST_URL = ud.join(URL, '%s/torrent1.htm')
    ID_REGEXP = re.compile(r'(\d{2,8}).html')
    PAGE_QUERY = 'torrent%d.htm'

    def handle_search(self, url, keyword):
        url.path = 's.php'
        url.update_qs('k=%s' % keyword)
        self.PAGE_QUERY = 'page=%d'

    def handle_page(self, url, num):
        if url.path == 's.php':
            url.update_qs(self.PAGE_QUERY % int(num))
        else:
            self.PAGE_QUERY = 'torrent%d.htm'
            path = url.path.split('/')
            url.path = '/{}/{}'.format(path[1], self.PAGE_QUERY % int(num))

    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        list_xpath = r'//a[@class="list_subject"]'
        for e in self.etree(r, encoding=self.encoding).xpath(list_xpath):
            try:
                title = e.text.strip()
                link = e.get('href')
                id_ = self.get_id_num(link)
                date = e.getparent().getnext().find('a').text.strip()
                yield {'id': id_, 'title': title, 'link': link, 'date': date}
            except:
                self.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        item_xpath = r'//a[contains(@href, "file_download")]'
        script_regexp = re.compile(r'javascript:file_download\([\'"](.*)[\'"]\,\s[\'"](.*)[\'"]\);')
        magnet_xpath = r'//input[contains(@value, "magnet:?xt")]'

        root = self.etree(r, encoding=self.encoding)

        for e in root.xpath(item_xpath):
            try:
                href = e.get('href')
                match = script_regexp.search(href)
                if match:
                    link = ud.join(self.URL, match.group(1))
                    name = match.group(2)
                    link_type = self.is_magnet(link)
                    yield {'name': name, 'link': link, 'type': link_type}
            except:
                self.trace_error()

        for e in root.xpath(magnet_xpath):
            try:
                value = e.get('value')
                query = ud.URL(value)
                xt = query.query_dict.get('xt', None)
                name = query.query_dict.get('dn')

                if xt and len(xt) > 10:
                    name = name if name else xt
                    yield {'name': name, 'link': ud.unquote(value), 'type': 'magnet'}
            except:
                self.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response
        return self.fetch(url, referer=ticket['referer'])
