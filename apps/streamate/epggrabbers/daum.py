# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Daum


class Daum(EpgGrabber):
    URL = 'https://www.daum.net'
    SEARCH_URL = 'https://search.daum.net/search?q=%s'
    id_required = False

    def get_programs(self, mapped_channel, proc_date, days):
        ch_name = mapped_channel.get('name')
        url = self.SEARCH_URL % '{}%20{}%20편성표'.format(proc_date.strftime('%Y년%m월%d일'), ch_name)
        response = self.fetch(url, referer=self.URL, follow_redirects=True)
        programs = self.parse_program(response.content, proc_date)
        return self.set_stop(programs, 3)

    def parse_program(self, content, proc_date):
        html = etree.HTML(content)
        date_index = {}
        for span in html.xpath('//span[contains(@id, "channelTitle")]/span[@class="date"]'):
            if span.text:
                month, day = span.text.split('.')
                span_date = dt(proc_date.year, int(month), int(day))
                if span_date.date() >= proc_date.date():
                    date_index[int(span.getparent().get('id')[-1])] = span_date

        for td in html.xpath('//td[contains(@id, "channelBody")]'):
            td_id = int(td.get('id')[-1])
            if td_id in date_index:
                hour = int(filter(str.isdigit, str(td.getparent().find('th').text.strip())))
                if td.find('dl/dt') is None: continue
                minute = int(td.find('dl/dt').text)
                start = date_index[td_id].replace(hour=hour, minute=minute, second=0)
                dd = td.find('dl/dd')
                if dd is None: continue
                if dd.find('a') is not None:
                    title_element = dd.find('a')
                else:
                    title_element = dd.find('span[@class=""]')
                title = title_element.text.strip()
                rerun = dd.xpath('span[contains(@class, "ico_re")]')
                rating = dd.xpath('span[contains(@class, "ico_rate")]')
                yield Program(dict(
                    title=unicode(title),
                    start=start,
                    rerun=True if rerun else False,
                    rating=filter(str.isdigit, str(rating[0].text)) if rating else None
                    ))
