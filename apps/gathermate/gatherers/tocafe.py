# -*- coding: utf-8 -*-

import re
import logging as log

from lxml import etree

from apps.gathermate.gatherer import Gatherer
from apps.common.exceptions import MyFlaskException
from apps.common import urldealer as ud
from apps.common import toolbox as tb

def register():
    return 'Gatherer'

class Tocafe(Gatherer):
    URL = 'https://tocafe.net'
    LIST_URL = ud.join(URL, 'bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,7})')
    SEARCH_QUERY = 'sca=&sop=and&sfl=wr_subject&stx=%s'
    PAGE_QUERY = 'page=%d'

    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        tree = self.etree(r, self.encoding)

        list_xpath = r'//div[@class="bo_tit"]/a'
        for e in tree.xpath(list_xpath):
            try:
                title = e.xpath('string()').strip() if e.xpath('string()') else 'No title.'
                link = e.get('href').strip() if e.get('href') else 'No link.'
                id_ = self.get_id_num(link)
                tr = e.getparent().getparent().getparent()
                volume = tr.find('td[2]').text
                date = tr.find('td[3]').text
                yield {'id': id_, 'title': title, 'link': link, 'etc': '{} {}'.format(volume, date)}
            except:
                MyFlaskException.trace_error()

        list_xpath = r'//div[@class="gall_con"]/div[2]'
        for e in tree.xpath(list_xpath):
            try:
                a = e.find('a[2]')
                title = a.xpath('string()').strip()
                link = a.get('href')
                id_ = self.get_id_num(link)
                category = e.find('a[1]').text.strip()
                volume = e.find('span[1]').text.strip()
                date = e.getparent().find('div[3]/span[2]/i').tail.strip()
                etc = '{} {} {}'.format(category, volume, date)

                yield {'id': id_, 'title': title, 'link': link, 'etc': etc}

            except:
                MyFlaskException.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        tree = self.etree(r, self.encoding)

        item_xpath = r'//section[@id="bo_v_file"]/h2/a'
        for e in tree.xpath(item_xpath):
            try:
                texts = e.xpath('string()')
                name = ' '.join(texts.split()[:-1])
                fname, ext = tb.get_ext(name)
                if fname == '[email protected]':
                    name = tb.cf_decode(e.find('span').get('data-cfemail'))
                if ext not in ['.smi', '.srt']:
                    name += '.torrent'
                link = ud.join(self.URL, e.get('href').strip())
                yield {'name': name, 'link': link, 'type': 'file'}
                section = e.getparent().getparent()
                magnet = section.find('ul/div/a[2]')
                if magnet is not None:
                    link = magnet.get('href')
                    yield {'name': name, 'link': link, 'type': 'magnet'}
            except:
                MyFlaskException.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Type[Dict[Text, Union[Text, List[Text]]]]) -> fetchers.Response
        return self.fetch(url, referer=ticket['referer'])
