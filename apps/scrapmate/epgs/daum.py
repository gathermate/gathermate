# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.scrapmate.scraper import EpgScraper

log = logging.getLogger(__name__)

def register():
    return 'Scraper', Daum


class Daum(EpgScraper):
    URL = 'https://www.daum.net'
    SEARCH_URL = 'https://m.search.daum.net/search?w=tot&q=%s'
    search_count = 0
    fail_count = 0

    def parse_html(self, html_str):
        for e in etree.HTML(html_str).xpath('//div[@class="tvlist_cont"]//div[@class="panel"]//div[@class="schedule_broadcast"]/ul/li'):
            start_time = e.find('.//span[@class="txt_time"]').text
            title = e.find('.//span[@class="txt_name"]').text
            yield start_time, unicode(title)

    def get_epg(self, ch_name, cid, days=1):
        self.search_count += 1
        proc_date = dt.today()
        epgs = {'name': ch_name, 'cid': cid, 'programs': [], 'from': 'daum'}
        for day in range(int(days)):
            url = self.SEARCH_URL % '{} {} 편성표'.format(proc_date.strftime('%Y년%m월%d일'), ch_name)
            response = self.fetch(url, referer=self.URL, follow_redirects=True)
            epgs['programs'] += self.get_info(response.content, proc_date)
            proc_date += datetime.timedelta(days=1)
        if len(epgs.get('programs')) > 0:
            return self.set_times(epgs)
        else:
            log.warning("Couldn't find epg for the channel : %s", ch_name)
            self.fail_count += 1
            return epgs
