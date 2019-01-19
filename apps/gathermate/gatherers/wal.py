# -*- coding: utf-8 -*-
import re

from apps.gathermate.gatherer import Gatherer
from apps.common.exceptions import MyFlaskException
from apps.common import urldealer as ud

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
        elif len(url.path) < 1:
            pass
        else:
            path = url.path.split('/')
            url.path = '/{}/{}'.format(path[1], self.PAGE_QUERY % int(num))

    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        tree = self.etree(r, encoding=self.encoding)

        list_xpath = r'//a[@class="list_subject"]'
        for e in tree.xpath(list_xpath):
            try:
                title = e.text.strip()
                link = e.get('href')
                id_ = self.get_id_num(link)
                date = e.getparent().getnext().find('a').text.strip()
                yield {'id': id_, 'title': title, 'link': link, 'etc': date}
            except:
                MyFlaskException.trace_error()

        pop_xpath = r'//div[@id="m_list"]/ul/li/a'
        root = tree.xpath(pop_xpath)
        length = len(root)
        for idx, e in enumerate(root):
            try:
                title = e.text.strip()
                link = e.get('href')
                id_ = length - idx
                real_id =  self.get_id_num(link)
                yield {'id': id_, 'title': title, 'link': link, 'etc': real_id}
            except:
                MyFlaskException.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        root = self.etree(r, encoding=self.encoding)

        item_xpath = r'//a[contains(@href, "file_download")]'
        script_regexp = re.compile(r'javascript:file_download\([\'"](.*)[\'"]\,\s[\'"](.*)[\'"]\);')
        for e in root.xpath(item_xpath):
            try:
                href = e.get('href')
                match = script_regexp.search(href)
                if match:
                    link = ud.join(self.URL, match.group(1))
                    name = match.group(2)
                    yield {'name': name, 'link': link, 'type': 'file'}
            except:
                MyFlaskException.trace_error()

        magnet_xpath = r'//input[contains(@value, "magnet:?xt")]'
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
                MyFlaskException.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response
        return self.fetch(url, referer=ticket['referer'])
