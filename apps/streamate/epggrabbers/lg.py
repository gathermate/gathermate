# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program

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

    def get_programs(self, mapped_channel, proc_date, days):
        lg_id = self.check_id(mapped_channel, 'lg')
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
            programs += self.parse_program(r.content.decode('euc-kr'), lg_id, proc_date)
            proc_date += datetime.timedelta(days=1)
        return self.set_stop(programs, 3)

    def parse_program(self, content, cid, proc_date):
        for tr in etree.HTML(content).xpath('//div[@class="tblType list"]/table/tbody/tr'):
            start_time = tr[0].text
            title = tr[1].text
            category = tr[2].text.strip().split('/')
            rating = tr[1][0].find('span[@class="tag cte_all"]').text
            yield Program(dict(
                cid=cid,
                title=unicode(title.strip()),
                start=dt.combine(proc_date, self.parse_time(start_time)),
                category=category,
                rating=rating,
                ))

