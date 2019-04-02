# -*- coding: utf-8 -*-
import re
import logging

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import MyFlaskException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

log = logging.getLogger(__name__)

def register():
    return 'Scraper', Wal


class Wal(BoardScraper):
    URL = 'https://torrentwal.com/'
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

        list_xpath = r'//table[@class="board_list"]/tr'
        for tr in tree.xpath(list_xpath):
            try:
                a = tr.find('td[@class="subject"]/a')
                link = a.get('href')
                title = a.text.strip()
                if a.getprevious() is not None:
                    title = a.getprevious().text + ' ' + title
                id_ = self.get_id_num(link)
                date = ''.join(tr.find('td[@class="datetime"]').itertext())
                yield {'id': id_, 'title': title, 'link': link, 'etc': date}
            except:
                MyFlaskException.trace_error()

        if ud.Url(r.url).path == '':
            pop_xpath = r'//ol[@id="latest_popular"]/li/a'
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

        item_xpath = r'//table[@id="file_table"]/tr/td/a'
        script_regexp = re.compile(r'javascript:file_download\(\'(.*?)\',.?\'(.*?)\'\)')
        location_regexp = re.compile(r'document.location.href=[\'"](.+)[\'"];')
        for a in root.xpath(item_xpath):
            try:
                href = a.get('href')
                match = script_regexp.search(href)
                if match:
                    second_link = ud.Url(ud.join(self.URL, match.group(1)))
                    if second_link.path.split('/')[-1].startswith('magnet'):
                        r = self.fetch(second_link, referer=r.url)
                        location_match = location_regexp.search(r.content)
                        if location_match:
                            link = location_match.group(1)
                            name = ud.split_qs(link)['dn']
                            yield {'name': name, 'link': link, 'type': 'magnet'}
                    else:
                        link = second_link.text
                        name = match.group(2)
                        yield {'name': name, 'link': link, 'type': 'file'}
                else:
                    link = ud.join(self.URL, href)
                    name = re.sub(r'\(.+\)$', '', a.xpath('string()').strip()).strip()
                    yield {'name': name, 'link': link, 'type': 'file'}
            except:
                MyFlaskException.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Type[Dict[Text, Union[Text, List[Text]]]]) -> fetchers.Response
        return self.fetch(url, referer=ticket['referer'])
