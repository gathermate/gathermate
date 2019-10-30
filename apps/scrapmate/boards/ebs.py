# -*- coding: utf-8 -*-
import re
import logging
import time
import json

from flask import url_for

from apps.scrapmate.scraper import BoardScraper
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'Scraper', Ebs

class Ebs(BoardScraper):
    courseId = 'ER2016G0BEG01ZZ'
    stepId = 'ET2016G0BEG0101'
    URL = 'http://home.ebse.co.kr/'
    '''
    http://home.ebse.co.kr/dumbenglish/replay/3/ajax/list?c.page=1&courseId=ER2016G0BEG01ZZ&stepId=ET2016G0BEG0101
    '''
    LIST_URL = ud.join(URL, '%s/replay/3/ajax/list?c.page=1&courseId=' + courseId + '&stepId=' + stepId)
    PAGE_QUERY = 'c.page=%d'
    # VOD http://m4str.ebse.co.kr/EW1M1901/ER2016G0BEG01ZZ/ET2016G0BEG0101/ET2016G0BEG0101_1000_1M.mp4
    VOD = 'http://m4str.ebse.co.kr/%s/%s/%s/%s_%s_1M.mp4' %('EW1M1901', courseId, stepId, stepId, '%s')

    GET_STREAM_URL = 'http://home.ebse.co.kr/dumbenglish/replay/3/ajax/getStreamUrl'
    def get_stream_url(self, lectId, referer):
        payload = {
            'lectId': lectId,
            'clsCd': 'V06',
            'mode': '',
        }
        r = self.fetch(self.GET_STREAM_URL, method='POST', payload=payload, referer=referer)
        js = json.loads(r.content)
        return js['url']

    def get_custom(self, query):
        url = ud.Url(self.LIST_URL % 'dumbenglish')

        self.length = 1004
        self.isRSS = True

        data = self.parse_list(url)

        yield '#EXTM3U\n'
        for article in sorted(data.items(), key=lambda item: int(item[0]), reverse=True):
            yield '#EXTINF:-1,%s\n%s\n' % (article[1]['title'], article[1]['link'])

    LECT_NUM_REGEXP = re.compile(r'lectNm_(.+)')
    def get_list(self, r):
        tree = self.etree(r, encoding=self.encoding)
        list_xpath = r'//div[@class="tbl_tbody"]/ul/li/div'
        for div in tree.xpath(list_xpath):
            try:
                _id = div.find('span[1]').text
                date = div.find('span[2]/i').tail
                a = div.find('strong/a')
                title = a.text.strip()
                lectNm = a.get('id')
                match = self.LECT_NUM_REGEXP.search(lectNm)
                if match:
                    lect_num = match.group(1)
                link = self.get_stream_url(lect_num, r.url)
                yield {'id': _id, 'title': '%s화 - %s' % (_id, title), 'link': link, 'date': date, 'lect_num': lect_num}
            except:
                GathermateException.trace_error()
        time.sleep(1)


