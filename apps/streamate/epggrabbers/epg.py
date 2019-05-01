# -*- coding: utf-8 -*-

import logging
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program
from apps.common import urldealer as ud

log = logging.getLogger()

def register():
    return 'EpgGrabber', Epgcokr


class Epgcokr(EpgGrabber):
    URL = None
    HOME_URL = 'http://www.epg.co.kr/'

    def __init__(self, fetcher):
        EpgGrabber.__init__(self, fetcher)
        if self.URL is None:
            self.set_url()

    def get_programs(self, mapped_channel, proc_date, days):
        epg_id = mapped_channel.get('epgcokr')
        url = ud.Url(self.URL.text)
        url.update_query({'c': epg_id})
        r = self.fetch(url, referer=self.HOME_URL)
        programs = self.parse_program(r.content.decode('euc-kr'), epg_id, proc_date)
        return self.set_stop(programs, 3)

    def set_url(self):
        a = etree.HTML(self.fetch(self.HOME_URL).content).xpath('//a[contains(@href, "tvguide")]')[0]
        Epgcokr.URL = ud.Url(a.get('href'))

    def parse_program(self, content, cid, proc_date):
        html = etree.HTML(content)
        date_index = {}
        for idx, td in enumerate(html.xpath('//table[@id="main_channel"]/tr/td')):
            if idx is 0: continue
            if td.find('center') is not None:
                digit = filter(str.isdigit, str(td.find('center').text))
                if digit:
                    month = digit[:2]
                    day = digit[-2:]
                    td_date = dt(proc_date.year, int(month), int(day))
                    if td_date.date() >= proc_date.date():
                        date_index[idx] = td_date
        for hour_tr in html.xpath('//table[@id="result_tbl"]/tr'):
            hour = int(hour_tr[0][0].get('id').split('_')[1])
            for index in date_index.iterkeys():
                for minute_tr in hour_tr[index].findall('table/tr'):
                    if len(minute_tr.getchildren()) < 2:
                        continue
                    minute = int(''.join(minute_tr[0].itertext()))
                    start = dt(date_index[index].year,
                               date_index[index].month,
                               date_index[index].day,
                               hour,
                               minute,
                               0)
                    title = ''.join(minute_tr[1].itertext()).strip()
                    rerun = None
                    rating = None
                    for img in minute_tr[1].findall('img'):
                        src_name = img.get('src').split('/')[-1].split('.')[0]
                        if src_name == 'nokid':
                            rating = 19
                        if src_name == 'rebroad':
                            rerun = True
                        if src_name.isdigit():
                            rating = int(src_name)
                    yield Program(dict(
                        cid=cid,
                        title=unicode(title),
                        start=start,
                        rerun=rerun,
                        rating=rating
                        ))

#for testing
if __name__ == '__main__':
    from apps.common import fetchers
    import app

    TEST_CHANNELS = [
        dict(cid='KBS1',name='KBS 1',chnum=9,kt=9,lg=501,sky=796,epg=9,pooq='K01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/9.png'),
    ]

    app = app.app
    epg = Epgcokr(fetchers.hire_fetcher())
    for program in epg.get_programs(TEST_CHANNELS[1], dt.today(), 1):
        print program

