# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt
import json
import time

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Oksusu


class Oksusu(EpgGrabber):
    URL = 'http://www.oksusu.com/'
    SEARCH_URL = 'http://www.oksusu.com/api/live/schedule?channelServiceId={cid}&startTime={start_ymdh}&endTime={end_ymdh}&scheduleKey=key&_={epoch_now}'
    PLAYER_URL = 'http://www.oksusu.com/v/%s'

    def get_programs(self, mapped_channel, proc_date, days):
        oksusu_id = mapped_channel.get('oksusu')
        programs = []
        for day in range(int(days)):
            date_str = dt.strftime(proc_date, '%Y%m%d')
            url = self.SEARCH_URL.format(cid=oksusu_id,
                                         start_ymdh=date_str + '00',
                                         end_ymdh=date_str + '24',
                                         epoch_now=int(time.time()*1000))
            r = self.fetch(url, referer=self.PLAYER_URL % oksusu_id, headers={'X-Requested-With': 'XMLHttpRequest'})
            js = json.loads(r.content)
            if js['result'] == 'OK':
                programs += self.parse_program(js['channel']['programs'], oksusu_id, proc_date)
            proc_date += datetime.timedelta(days=1)
        return programs

    def parse_program(self, content, cid, proc_date):
        for p in content:
            rerun = True if p['pgmRebroadYn'] == '1' else False
            yield Program(dict(cid=cid,
                               title=p['programName'],
                               sub_title='',
                               start=dt.strptime(p['startTimeYMDHIS'], '%Y%m%d%H%M%S'),
                               stop=dt.strptime(p['endTimeYMDHIS'], '%Y%m%d%H%M%S'),
                               rating=p['ratingCd'],
                               description=p['synopsis'],
                               category=p['mainGenreName'].split('/') if p['mainGenreName'] else '',
                               ))
