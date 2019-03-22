# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt
import json

from apps.streamate.epggrabber import EpgGrabber

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Sky


class Sky(EpgGrabber):

    URL = 'https://skylife.co.kr'
    PRE_URL = 'https://skylife.co.kr/channel/channel_number/channelAll.do'
    SEARCH_URL = 'https://skylife.co.kr/channel/epglist/channelScheduleListJson.do'
    EPG_SEARCH_TYPE = 'id'
    search_count = 0
    fail_count = 0

    def get_epg(self, mapped_channel, days=1):
        sky_id = self.check_id(mapped_channel, 'sky')
        if not sky_id: return []
        self.search_count += 1
        proc_date = dt.today()
        programs = []
        for day in range(days):
            payload = dict(area='in',
                           indate_type='now' if day is 1 else 'next',
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
            plist = js.get('scheduleListIn')
            for p in plist:
                programs.append({
                    'start': p['starttime'] + ' +0900',
                    'stop': p['endtime'] + ' +0900',
                    'title': p['program_name'],
                })
            if day > 1:
                proc_date += datetime.timedelta(days=1)
        return programs
