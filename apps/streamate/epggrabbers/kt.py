# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program

log = logging.getLogger()

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

    def get_programs(self, mapped_channel, proc_date, days):
        kt_id = mapped_channel.get('kt')
        programs = []
        for day in range(days):
            payload = dict(ch_type=1, view_type=1, service_ch_no=kt_id, seldate=proc_date.strftime('%Y%m%d'))
            r = self.fetch(self.SEARCH_URL, referer=self.URL, payload=payload, method='POST')
            programs += self.parse_program(r.content.decode('euc-kr'), kt_id, proc_date)
            proc_date += datetime.timedelta(days=1)
        return self.set_stop(programs, 3)

    def parse_program(self, content, cid, proc_date):
        for e in etree.HTML(content).xpath('//div[@class="tableSchedule"]/ul/li[contains(@class, "lists")]'):
            hour = e.find('div[@class="hour"]').text
            for div in e.find('div[@class="data"]').iterchildren():
                minute = div.find('div[@class="minute"]').text
                info = div.find('div[@class="name"]/div[@class="info"]')
                title = info.find('span[@class="text"]').xpath('string()')
                rating = info.find('span[@class="icon"]/img[1]').get('alt')
                category = div.find('div[@class="type"]').text.split('/')
                yield Program(dict(cid=cid,
                                   title=unicode(title.strip()),
                                   start=dt.combine(proc_date, self.parse_time('%s:%s' % (hour, minute))),
                                   stop='',
                                   rating=rating,
                                   category=category))