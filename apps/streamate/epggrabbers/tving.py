# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt
import json

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program
from apps.streamate.streamers import tving
from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Tving


class Tving(EpgGrabber):
    URL = tving.Tving.BASE_URL
    API_URL = tving.Tving.API_URL
    API_KEY = tving.Tving.API_KEY
    PLAYER_URL = tving.Tving.PLAYER_URL
    CS = tving.Tving.CS

    def get_programs(self, mapped_channel, proc_date, days):
        tving_id = mapped_channel.get('tving')
        schedules = self.api_epg(tving_id, days if days is not None else 1)
        programs = []
        if schedules:
            for schedule in schedules:
                for program in schedule:
                    programs.append(
                        Program(dict(
                            cid=tving_id,
                            title=program['episode']['name']['ko'] if program['episode'] else program['program']['name']['ko'],
                            start=dt.strptime(str(program['broadcast_start_time']), '%Y%m%d%H%M%S'),
                            stop=dt.strptime(str(program['broadcast_end_time']), '%Y%m%d%H%M%S'),
                            rerun=True if program['rerun_yn'] == 'Y' else False,
                            category=program['episode']['category1_name']['ko'].split('/') if program['episode'] else program['program']['category1_name']['ko'].split('/'),
                            episode=program['episode']['frequency'] if program['episode'] else None,
                            description=program['episode']['synopsis']['ko'] if program['episode'] else program['program']['synopsis']['ko'],
                            ))
                        )
        return programs

    def api_epg(self, cid, days):
        url = ud.Url(self.API_URL + '/media/schedules')
        url.update_query(dict(
            apiKey=self.API_KEY.get('mobile'),
            pageNo=1,
            pageSize=20,
            order='chno',
            scope='all',
            adult='n',
            free='all',
            channelCode=cid,
            screenCode=self.CS.get('screenCode'), teleCode=self.CS.get('teleCode'),
            networkCode=self.CS.get('networkCode'), osCode=self.CS.get('osCode'),
            )
        )
        broadDate = dt.today().date()
        for _ in range(days):
            broadTime = 0
            for _ in range(8):
                url.query_dict['broadDate'] = dt.strftime(broadDate, '%Y%m%d')
                url.query_dict['broadcastDate'] = dt.strftime(broadDate, '%Y%m%d')
                url.query_dict['startBroadTime'] = '%02d0000' % broadTime
                url.query_dict['endBroadTime'] = '%02d0000' % int(broadTime + 3)
                r = self.fetch(url, referer=self.PLAYER_URL % cid)
                js = json.loads(r.content)
                try:
                    yield js['body']['result'][0]['schedules']
                except Exception as e:
                    log.error(e.message)
                broadTime += 3
            broadDate += datetime.timedelta(days=1)