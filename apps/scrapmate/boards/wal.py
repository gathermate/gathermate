# -*- coding: utf-8 -*-
import re
import logging
import time
import base64
import random
import math
import json

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'Scraper', Wal


class Wal(BoardScraper):
    URL = 'https://torrentwal.com/'
    LIST_URL = ud.join(URL, '%s/torrent1.htm')
    ID_REGEXP = re.compile(r'(\d{2,8}).html')
    PAGE_QUERY = 'torrent%d.htm'

    def handle_search(self, url, keyword):
        url.path = 'bbs/s.php'
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

    S_READ_REGEXP = re.compile(r'\("(.+?)",\s"(.+?)"\)')
    CATEGORY_REGEXP = re.compile(r'^\[(.*?)\]')
    def get_list(self, r):
        tree = self.etree(r, encoding=self.encoding)
        list_xpath = r'//table[@class="board_list"]/tr'
        for tr in tree.xpath(list_xpath):
            try:
                if tr.get('style') == 'display:none':
                    continue
                td = tr.find('td[@class="subject"]')
                a_list = td.findall('a')
                if len(a_list) > 0:
                    a = td.findall('a')[-1]
                else:
                    continue
                link = a.get('href')
                id_ = self.get_id_num(link)
                if id_ < 0:
                    match = self.S_READ_REGEXP.search(str(a.get('onclick')))
                    if match:
                        board = match.group(1)
                        id_ = int(match.group(2))
                        link = '/bbs/view_mid.php?bo_table={:s}&wr_id={:d}'.format(board, id_)
                title = a.text.strip()
                date = ''.join(tr.find('td[@class="datetime"]').itertext())
                vol = ''.join(tr.find('td[@class="hit"]').itertext())
                td.remove(a)
                info = ' '.join([child.text for child in td.getchildren() if child.text is not None] + [''.join(vol.split(' ')), date])
                yield {'id': id_, 'title': title, 'link': link, 'etc': re.sub('[\[\]]', '', info)}
            except:
                GathermateException.trace_error()
        if ud.Url(r.url).path == '':
            pop_xpath = r'//ol[@id="latest_popular"]/li/a'
            root = tree.xpath(pop_xpath)
            length = len(root)
            for idx, e in enumerate(root):
                try:
                    title = re.sub(self.CATEGORY_REGEXP, '', e.text.strip())
                    match = self.CATEGORY_REGEXP.search(e.text.strip())
                    cate = match.group(1) if match is not None else '기타'
                    link = e.get('href')
                    id_ = length - idx
                    info = '%d %s' % (self.get_id_num(link), cate)
                    yield {'id': id_, 'title': title, 'link': link, 'etc': info}
                except:
                    GathermateException.trace_error()

    SCRIPT_REGEXP = re.compile(r'\'(.+?)\'')
    ITEM_XPATH = r'//table[@id="file_table"]//a'
    LOCATION_REGEXP = re.compile(r'document.location.href=[\'"](.+)[\'"];')
    def get_item(self, r):
        root = self.etree(r, encoding=self.encoding)
        for a in root.xpath(self.ITEM_XPATH):
            try:
                name = re.sub(r'\((?:.(?!\())+$', '', a.xpath('string()').strip()).strip()
                onclick = a.get('onclick')
                if onclick:
                    match = self.SCRIPT_REGEXP.search(onclick)
                    if match:
                        link = match.group(1)
                        yield {'name': name, 'link': link, 'type': 'file'}
                        continue
                href = a.get('href')
                matches = self.SCRIPT_REGEXP.findall(href)
                if matches:
                    link = matches[0]
                    if 'magnet' in link:
                        magnet_page = ud.Url(ud.join(self.URL, link))
                        magnet_r = self.fetch(magnet_page, referer=r.url)
                        location_match = self.LOCATION_REGEXP.search(magnet_r.content)
                        if location_match:
                            link = location_match.group(1)
                            sub_name = ud.split_qs(link)['dn']
                            yield {'name': sub_name, 'link': link, 'type': 'magnet'}
                    else:
                        if len(matches) > 1:
                            yield {'name': matches[1], 'link': link, 'type': 'file'}
                        else:
                            yield {'name': name, 'link': link, 'type': 'file'}
                else:
                    yield {'name': name, 'link': href, 'type': 'file'}

            except:
                GathermateException.trace_error()


    def get_file(self, url, ticket):
        return self.fetch(url, referer=ticket['referer'])

    FORM_XPATH = r'//form[@id="Down"]'
    CAPTCHA_XPATH = r'//a[@id="TencentCaptcha"]'
    NEWURL_REGEXP = re.compile(r'var.newUrl.=.\'(.+)\';')
    def get_filetender(self, url, ticket):
        r = self.fetch(url,
                       referer=ticket['referer'])
        tree = self.etree(r, self.encoding)
        forms = tree.xpath(self.FORM_XPATH)
        inputs = {inpt.get('name'): inpt.get('value') for form in forms for inpt in form.findall('.//input')}

        down_url = self.NEWURL_REGEXP.search(r.content).group(1)
        if not 'filetender' in down_url:
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
        down_url = ud.Url(down_url).update_query(inputs)
        log.info("Wait for Linktender's countdown...")
        time.sleep(3)
        log.info('Start download on Linktender...')
        return self.fetch(down_url, referer=url.text)