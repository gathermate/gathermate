# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Kt


class Kt(EpgGrabber):
    '''
    ch_type: 1 # (1, olleh tv live @ olleh tv), (2, skylife @ olleh tv), (3, olleh tv live @ olleh UHD tv), (4, skylife @ olleh UHD tv)
    view_type: 1 (1, day), (2, week)
    service_ch_no: 13
    seldate: 20190321
    '''
    URL = 'https://m.tv.kt.com'
    SEARCH_URL = 'https://m.tv.kt.com/tv/channel/mSchedule.asp'
    EPG_SEARCH_TYPE = 'id'
    search_count = 0
    fail_count = 0

    def get_epg(self, mapped_channel, days=1):
        kt_id = mapped_channel.get('kt')
        if kt_id is None:
            log.warning("Couldn't find epg for the channel : %s", mapped_channel.get('name'))
            return []
        self.search_count += 1
        proc_date = dt.today()
        programs = []
        for day in range(int(days)):
            payload = dict(ch_type=1, view_type=1, service_ch_no=kt_id, seldate=proc_date.strftime('%Y%m%d'))
            r = self.fetch(self.SEARCH_URL, referer=self.URL, payload=payload, method='POST')
            programs += self.get_epg_info(r.content.decode('euc-kr'), proc_date)
            proc_date += datetime.timedelta(days=1)
        if len(programs) > 0:
            return self.set_epg_times(programs)
        else:
            log.warning("Couldn't find epg for the channel : %s", mapped_channel.get('name'))
            self.fail_count += 1
            return programs

    def parse_epg_html(self, html_str):
        for e in etree.HTML(html_str).xpath('//div[@class="tableSchedule"]/ul/li[@class="lists"]'):
            hour = e.find('div[@class="hour"]').text
            for div in e.find('div[@class="data"]').iterchildren():
                minute = div.find('div[@class="minute"]').text
                title = div.find('div[@class="name"]/div/span').text
                yield '%s:%s' % (hour, minute), unicode(title)