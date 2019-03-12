# -*- coding: utf-8 -*-

import logging
import re
import json

from apps.scrapmate.scraper import EpgScraper
from apps.streamate.streamer import Channel

log = logging.getLogger(__name__)

def register():
    return 'Scraper', KtEpg

class KtEpg(EpgScraper):
    URL = 'https://www.kt.com'
    CHANNELS_URL = 'https://tv.kt.com/tv/channel/pChInfo.asp'
    CH_NUM_NAME_REGEXP = re.compile(r'(\d{1,4})[\xa0\s](.*)')

    def channels(self):
        etree = self.fetch_and_etree(self.CHANNELS_URL, referer=self.URL, encoding='euc-kr')
        channels = {}
        for e in etree.xpath('//div[@id="listChannelPanel"]/ul/li/a/span'):
            match = self.CH_NUM_NAME_REGEXP.search(e.text.strip())
            channels[match.group(1)] = match.group(2)

        r = self.fetch('https://tv.kt.com/tv/channel/pSchedule.asp',
                   payload=dict(ch_type=1,
                                service_ch_no=1,
                                view_type=2,
                                seldate=20190312),
                   method='POST')

        return r.content.decode('euc-kr')



'''
pooq.K01
kt.csa
'''

