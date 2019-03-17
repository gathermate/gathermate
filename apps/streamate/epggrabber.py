# -*- coding: utf-8 -*-

import datetime
from datetime import datetime as dt

class EpgGrabber(object):

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def fetch(self, url, cached=False, **kwargs):
        return self.fetcher.fetch(url, cached=cached, **kwargs)

    def set_times(self, epgs):
        programs = sorted(epgs.get('programs'), key=lambda item: item.get('start'))
        for idx, p in enumerate(programs):
            if idx + 1 < len(programs):
                p['stop'] = programs[idx + 1].get('start')
            else:
                p['stop'] = p['start'] + datetime.timedelta(hours=3)
                '''
                p['stop'] = dt.combine(p['start'].date() + datetime.timedelta(days=1),
                                       datetime.time(00, 00))
                '''
            p['start'] = dt.strftime(p['start'], '%Y%m%d%H%M%S') + ' +0900'
            p['stop'] = dt.strftime(p['stop'], '%Y%m%d%H%M%S') + ' +0900'
        epgs['programs'] = programs
        return epgs

    def parse_time(self, time_str, time_format='%H:%M'):
        return dt.strptime(time_str, time_format).time()


    def get_info(self, raw_html, proc_date):
        programs = []
        for start_time, title in self.parse_html(raw_html):
            start_time = self.parse_time(start_time)
            start_datetime = dt.combine(proc_date, start_time)
            programs.append({
                'start': start_datetime,
                'stop': '',
                'title': title,
            })
        return programs

