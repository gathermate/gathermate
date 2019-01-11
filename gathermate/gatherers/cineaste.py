# -*- coding: utf-8 -*-
import re
import time

from gathermate.gatherer import Gatherer
from gathermate.exception import GathermateException as GE
from util import urldealer as ud

def register():
    return 'Gatherer'

class Cineaste(Gatherer):
    URL = "http://cineaste.co.kr"
    LIST_URL = ud.join(URL, '/bbs/board.php?bo_table=%s')
    ID_REGEXP = re.compile(r'wr_id=(\d{2,8})')
    SEARCH_QUERY = 'sca=&mv_no=&sfl=wr_subject&stx=%s&sop=and'
    PAGE_QUERY = 'page=%d'

    def set_login(self, config):
        self.login_info = {
            'payload': {
                'mb_id': config.get('mb_id'),
                'mb_password': config.get('mb_password'),
                'url': 'http://cineaste.co.kr',
            },
            'url': 'https://cineaste.co.kr:443/bbs/login_check.php',
            'denied': re.compile(r'다음 항목에 오류가 있습니다.'),
        }

    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        list_xpath = r'//td[@class="list-subject"]/a'
        #댓글17개
        cmt_regexp = re.compile(ur'댓글(\d{1,10})개')
        for e in self.etree(r, encoding=self.encoding).xpath(list_xpath):
            try:
                title = cmt_regexp.sub('', e.xpath('string()').strip())
                link = e.get('href').strip()
                id_ = self.get_id_num(link)
                lang = e.getparent().getparent().find('td[2]/a/span/b').text.strip()
                date = e.getparent().getparent().find('td[7]').text.strip()
                etc = '{} {}'.format(date, lang)
                yield {'id': id_, 'title': title, 'link': link, 'etc': etc}
            except:
                GE.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        root = self.etree(r, encoding=self.encoding)

        title_regexp = re.compile(r'\s\(\d+.*\)')
        item_xpath = r'//a[contains(@class, "list-group-item") and contains(@href, "download")]'
        for e in root.xpath(item_xpath):
            try:
                name = title_regexp.sub('', e.xpath('text()')[0]).strip()

                link = e.get('href')
                link_type = self.is_magnet(link)
                etc = ''
                yield {'name': name, 'link': link, 'type': link_type, 'etc': etc}
            except:
                GE.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response
        self.fetch(url, referer=ticket['referer'])
        old_url = url.text
        url.query_dict['ds'] = 1
        url.query_dict['js'] = 'on'
        time.sleep(1)
        return self.fetch(url, referer=old_url)