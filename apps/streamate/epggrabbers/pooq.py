# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt
import json

from apps.streamate.epggrabber import EpgGrabber
from apps.streamate.epggrabber import Program
from apps.streamate.streamers import pooq
from apps.common import urldealer as ud

log = logging.getLogger(__name__)

def register():
    return 'EpgGrabber', Pooq


class Pooq(EpgGrabber):
    URL = pooq.Pooq.BASE_URL
    API_URL = pooq.Pooq.API_URL
    API_QUERY = pooq.Pooq.API_QUERY
    PLAYER_URL = pooq.Pooq.PLAYER_URL

    def get_programs(self, mapped_channel, proc_date, days):
        pooq_id = mapped_channel.get('pooq')
        info = self.api_epg(pooq_id, days if days is not None else 1)
        programs = []
        if info:
            for program in info.get('list'):
                programs.append(
                    Program(dict(
                        cid=pooq_id,
                        title=program.get('title'),
                        start=dt.strptime(program.get('starttime'), '%Y-%m-%d %H:%M'),
                        stop=dt.strptime(program.get('endtime'), '%Y-%m-%d %H:%M'),
                        ))
                    )
        return programs

    def api_epg(self, cid, days):
        api = ud.Url(ud.join(self.API_URL, '/live/epgs/channels/%s' % cid))
        stime = dt.strftime(dt.today(), '%Y-%m-%d %H:%M')
        etime = dt.strftime(dt.today() + datetime.timedelta(days=days), '%Y-%m-%d %H:%M')
        query = dict(startdatetime=stime, enddatetime=etime, offset=0, limit=999, orderby='old')
        api.update_query(query)
        response = self.fetch(api, referer=self.PLAYER_URL % cid)
        return json.loads(response.content)
