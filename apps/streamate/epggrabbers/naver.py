# -*- coding: utf-8 -*-

import logging
import re
import json
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'EpgGrabber', Naver


class Naver(EpgGrabber):
    URL = 'https://m.naver.com'
    SEARCH_URL = 'https://m.search.naver.com/search.naver?query=%s'
    id_required = False

    def get_programs(self, mapped_channel, proc_date, days):
        ch_name = mapped_channel.get('name')
        keyword = mapped_channel.get('naver') if mapped_channel.get('naver') else ch_name + ' 편성표'
        url = self.SEARCH_URL % ud.quote(keyword)
        api_config = self._get_api_config(self.fetch(url, referer=self.URL))
        if 'url' in api_config and 'scheduleParam' in api_config:
            programs = self.parse_program(api_config, proc_date, days)
            return self.set_stop(programs)
        return []

    def parse_program(self, api_config, proc_date, days):
        api_url = ud.Url(api_config.get('url'))
        api_url.update_query(api_config.get('scheduleParam'))
        for day in range(days):
            api_url.query_dict['u2'] = dt.strftime(proc_date, '%Y%m%d')
            response = self.fetch(api_url, referer=self.URL)
            data = json.loads(response.content)
            if data.get('statusCode', None) == 'SUCCESS':
                for item in data.get('dataHtml'):
                    for e in etree.HTML(item).xpath('//div[@class="inner"]'):
                        start_time = e.find('div[1]').text
                        pr_info = e.find('div[2]')
                        pr_title = pr_info.find('div[2]')
                        title = pr_title.xpath('string()').strip()
                        sub_info = e.find('div[@class="sub_info"]/span')
                        icon_area = pr_info.find('div[@class="icon_area"]')
                        rerun = icon_area.find('span[@class="state_ico re"]')
                        yield Program(dict(
                            title=unicode(title),
                            sub_title=sub_info.text if sub_info is not None else None,
                            start=dt.combine(proc_date, self.parse_time(start_time)),
                            rerun=True if rerun is not None else False,
                            ))

            proc_date += datetime.timedelta(days=1)

    def _get_api_config(self, response):
        match = re.search(r'apiConfig:\s({.+u2:\s"\d+"\s}\s})', response.content)
        if match is not None:
            return json.loads(re.sub(r'(\w+):\s', r'"\1":', match.group(1)))
        return {}

