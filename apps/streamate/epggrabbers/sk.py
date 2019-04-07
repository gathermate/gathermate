# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program

log = logging.getLogger(__name__)

class Sk(EpgGrabber):
    '''
    접속 지연..... 파밍 불가
    var currDate = $("#key_depth3").val();
    http://www.skbroadband.com/content/realtime/Channel_List.do
    retUrl:
    pageIndex: 1
    pack: (unable to decode value)
    key_depth1: 5100
    key_depth2: 14
    key_depth3:
    key_chno:
    key_depth2_name:
    tab_gubun: 1
    menu_id: D03020000
    '''
    URL = 'http://www.skbroadband.com/'
    SEARCH_URL = 'http://skbroadband.com/content/realtime/Channel_List.do'
    RATING = {6: 12, 7: 15, 8: 19}

    def get_programs(self, mapped_channel, proc_date, days):
        sk_id = str(mapped_channel.get('sk'))
        key_depth1, key_depth2 = sk_id.split('.')
        programs = []
        for day in range(days):
            payload = dict(key_depth1=key_depth1,
                           key_depth2=key_depth2,
                           key_depth3=dt.strftime(proc_date, '%Y%m%d'),
                           )
            r = self.fetch(self.SEARCH_URL, referer=self.URL, method='POST', payload=payload)
            programs += self.parse_program(r.content.decode('euc-kr'), sk_id, proc_date)
            proc_date += datetime.timedelta(days=1)
        return self.set_stop(programs, 3)

    def parse_program(self, content, cid, proc_date):
        for li in etree.HTML(content).xpath('//div[@class="organization_list"]//ol/li'):
            p1 = li.find('p[1]')
            p2 = li.find('p[2]')
            icons = p2.findall('span/span')
            rating = 0
            for icon in icons:
                flag = int(filter(str.isdigit, icon.get('class')))
                if flag in self.RATING:
                    rating = self.RATING[flag]
                    break
            yield Program(dict(
                title=unicode(p2.text.strip()),
                start=dt.combine(proc_date, self.parse_time(p1.text)),
                rating=rating,
            ))



#for testing

if __name__ == '__main__':
    from apps.common import fetchers
    import app

    TEST_CHANNELS = [
        dict(cid='KBS1',name='KBS 1',chnum=9,sk=5100.11,epgcokr=9,kt=9,lg=501,sky=796,pooq='K01',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/9.png'),
        dict(cid='KBS2',name='KBS 2',chnum=7,sk=5100.12,epgcokr=7,kt=7,lg=502,sky=795,pooq='K02',logo='https://tv.kt.com/relatedmaterial/ch_logo/live/7.png'),
    ]
    fetcher = fetchers.hire_fetcher()
    sk = Sk(fetcher)
    programs = sk.get_programs(TEST_CHANNELS[0], dt.today(), 1)
    for p in programs:
        print('{} - {} - {}'.format(p.start, p.title, p.rating))
