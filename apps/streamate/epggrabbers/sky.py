# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt
import json

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program

log = logging.getLogger()

def register():
    return 'EpgGrabber', Sky


class Sky(EpgGrabber):

    URL = 'https://skylife.co.kr'
    PRE_URL = 'https://skylife.co.kr/channel/channel_number/channelAll.do'
    SEARCH_URL = 'https://skylife.co.kr/channel/epglist/channelScheduleListJson.do'

    def get_programs(self, mapped_channel, proc_date, days):
        sky_id = mapped_channel.get('sky')
        programs = []
        for day in range(days):
            payload = dict(area='in',
                           indate_type='now' if day is 0 else 'next',
                           inairdate=proc_date.strftime('%Y-%m-%d'),
                           inFd_channel_id=sky_id)
            for _ in range(2):
                r = self.fetch(self.SEARCH_URL,
                               method='POST',
                               payload=payload)
                js = json.loads(r.content)
                if js: break
                self.fetch(self.PRE_URL)
            if not js:
                log.warning('No JSON data.')
                continue
            programs += self.parse_program(js.get('scheduleListIn', []), sky_id, proc_date)
            if day > 0:
                proc_date += datetime.timedelta(days=1)
        return programs

    def parse_program(self, content, cid, proc_date):
        for p in content:
            yield Program(dict(cid=cid,
                               title=p['program_name'],
                               sub_title=p['program_subname'],
                               start=dt.strptime(p['starttime'], '%Y%m%d%H%M%S'),
                               stop=dt.strptime(p['endtime'], '%Y%m%d%H%M%S'),
                               rating=p['grade'],
                               description=p['description'],
                               category=p['program_category1'].split('/') + p['program_category2'].split('/'),
                               rerun=True if p['rebroad'] == 'Y' else False,
                               episode=p['episode_id']))
