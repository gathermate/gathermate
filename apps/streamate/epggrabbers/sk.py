# -*- coding: utf-8 -*-

import logging
import datetime
from datetime import datetime as dt

from lxml import etree

from apps.streamate.epggrabber import EpgGrabber

log = logging.getLogger(__name__)

class Sk(EpgGrabber):
    pass
    '''
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

'''
#for testing

from apps.common import fetchers
import app

TEST_CHANNELS = [
    dict(cid='ANIBOX-1',name='ANIBOX',chnum=993,kt=993,lg=695,sky=84,pooq='C4401',logo='http://img.pooq.co.kr/BMS/ChannelImg/32_애니박스.png'),
    dict(cid='ANIMAX-1',name='애니맥스',chnum=155,kt=995,lg=703,sky=725,pooq='A01',logo='http://img.pooq.co.kr/BMS/ChannelImg/31_anymax.png'),
]

if __name__ == '__main__':

    sk = Sk(fetchers.hire_fetcher())
    print(sk.get_epg(TEST_CHANNELS[0]), 2)
'''
