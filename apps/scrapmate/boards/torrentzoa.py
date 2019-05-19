# -*- coding: utf-8 -*-
import time
import logging
import re

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'Scraper', Torrentzoa


class Torrentzoa(BoardScraper):
    URL = "https://www.torrentzoa.com/"
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