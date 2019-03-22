# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Lg


class Lg(EpgGrabber):
    '''
    chnlCd: 504
    evntCmpYmd: 20190321
    yesterdayYmd: 20190320
    tomorrowYmd: 20190322
    '''
    URL = 'http://www.uplus.co.kr'
    SEARCH_URL = 'http://www.uplus.co.kr/css/chgi/chgi/RetrieveTvSchedule.hpi'
    EPG_SEARCH_TYPE = 'id'
    search_count = 0
    fail_count = 0

    def get_epg(self, mapped_channel, days=1):
        lg_id = self.check_id(mapped_channel, 'lg')
        if not lg_id: return []
        self.search_count += 1
        proc_date = dt.today()
        programs = []
        for day in range(int(days)):
            payload = dict(chnlCd=lg_id,
                           evntCmpYmd=proc_date.strftime('%Y%m%d'),
                           yesterdayYmd=(proc_date - datetime.timedelta(days=1)).strftime('%Y%m%d'),
                           tomorrowYmd=(proc_date + datetime.timedelta(days=1)).strftime('%Y%m%d'))
            r = self.fetch(self.SEARCH_URL,
                           method='POST',
                           referer='http://www.uplus.co.kr/css/chgi/chgi/RetrieveTvContentsMFamily.hpi',
                           payload=payload,
                           headers={'HPI_AJAX_TYPE': 'ajaxCommSubmit', 'HPI_HTTP_TYPE': 'ajax', 'X-Requested-With': 'XMLHttpRequest'})
            programs += self.get_epg_info(r.content.decode('euc-kr'), proc_date)
            proc_date += datetime.timedelta(days=1)
        if programs:
            return self.set_epg_times(programs)
        else:
            log.warning("Couldn't find epg for the channel : %s", mapped_channel.get('name'))
            self.fail_count += 1
            return programs

    def parse_epg_html(self, html_str):
        for tr in etree.HTML(html_str).xpath('//div[@class="tblType list"]/table/tbody/tr'):
            start_time = tr.find('td[@class="txtC"]').text
            title = tr.find('td[@class="txtL"]').text
            yield start_time, unicode(title.strip())
