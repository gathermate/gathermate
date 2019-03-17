# -*- coding: utf-8 -*-

import logging
import re
import json
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Naver


class Naver(EpgGrabber):
    URL = 'https://m.naver.com'
    SEARCH_URL = 'https://m.search.naver.com/search.naver?query=%s'
    search_count = 0
    fail_count = 0

    def parse_html(self, html_str):
        for e in etree.HTML(html_str).xpath('//div[@class="inner"]'):
            start_time = e.find('div[1]').text
            pr_info = e.find('div[2]')
            pr_title = pr_info.find('div[2]')
            sub_info = e.find('div[@class="sub_info"]/span')
            title = pr_title.xpath('string()').strip()
            if sub_info is not None:
                title = '{} {}'.format(title, sub_info.text)
            yield start_time, unicode(title)

    def _get_api_config(self, response):
        match = re.search(r'apiConfig:\s({.+u2:\s"\d+"\s}\s})', response.content)
        if match is not None:
            return json.loads(re.sub(r'(\w+):\s', r'"\1":', match.group(1)))
        return {}

    def get_epg(self, ch_name, cid, days=1):
        self.search_count += 1
        url = self.SEARCH_URL % ch_name + ' 편성표'
        api_config = self._get_api_config(self.fetch(url, referer=self.URL))
        epgs = {'name': ch_name, 'cid': cid, 'programs': [], 'from': 'naver'}
        if 'url' in api_config and 'scheduleParam' in api_config:
            api_url = ud.Url(api_config.get('url'))
            api_url.update_query(api_config.get('scheduleParam'))
            proc_date = dt.strptime(api_config.get('scheduleParam').get('u2'), '%Y%m%d').date()
            for day in range(int(days)):
                api_url.query_dict['u2'] = dt.strftime(proc_date, '%Y%m%d')
                response = self.fetch(api_url, referer=url)
                data = json.loads(response.content)
                if data.get('statusCode', None) == 'SUCCESS':
                    for item in data.get('dataHtml'):
                        epgs['programs'] += self.get_info(item, proc_date)
                proc_date += datetime.timedelta(days=1)
            return self.set_times(epgs)
        else:
            log.warning("Couldn't find epg for the channel : %s", ch_name)
            self.fail_count += 1
            return epgs
