# -*- coding: utf-8 -*-

import datetime
from datetime import datetime as dt
import logging
import heapq
import itertools
import threading

from concurrent import futures

log = logging.getLogger(__name__)
lock = threading.RLock()

def get_epg(channel_map, grabbers, days=1):
    pq = PriorityQueue()
    for grabber in grabbers:
        grabber.gcounter = 0
        pq.set(grabber.__class__.__name__.lower(), grabber)
    future_list = []
    with futures.ThreadPoolExecutor(max_workers=8) as exe:
        for ch in channel_map:
            future_list.append(exe.submit(set_epg, ch, days, pq))
    for f in future_list:
        yield f.result()
    log.debug('\n' + '\n'.join(['%s : priority(%d), age(%d)' % (n.upper(), p, c) for p, c, n, _ in pq.entries.values()]) + '\n')

def set_epg(mapped_channel, days, pq):
    epg = dict(fails=[], programs=[], source=None)
    mapped_channel['epg'] = epg
    only = mapped_channel.get('only')
    skip = mapped_channel.get('skip')
    skip = skip.split('|') if skip else []
    if only:
        for o in only.split('|'):
            try:
                with lock: grabber = pq.get(o)
            except KeyError as ke:
                log.error('%s is required to grab %s', ke.message.capitalize(), mapped_channel['name'])
                return mapped_channel
            epg['programs'] = grabber.get_epg(mapped_channel, days)
            if epg['programs']: break
            epg['fails'].append(grabber.__class__.__name__)
    else:
        while len(skip) < pq.size():
            with lock:
                name, grabber = pq.except_get(skip)
            skip.append(name)
            if grabber.EPG_SEARCH_TYPE == 'id' and mapped_channel.get(name) is None:
                with lock: pq.de_priority(name)
                continue
            epg['programs'] = grabber.get_epg(mapped_channel, days)
            if epg['programs']: break
            epg['fails'].append(name)
    if epg['programs']:
        epg['source'] = grabber.__class__.__name__
    return mapped_channel


class EpgGrabber(object):

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def fetch(self, url, cached=False, **kwargs):
        return self.fetcher.fetch(url, cached=cached, **kwargs)

    def set_epg_times(self, programs):
        programs = sorted(programs, key=lambda item: item.get('start'))
        for idx, p in enumerate(programs):
            if idx + 1 < len(programs):
                p['stop'] = programs[idx + 1].get('start')
            else:
                # give 3 hours to the last program duration.
                p['stop'] = p['start'] + datetime.timedelta(hours=3)
                '''
                p['stop'] = dt.combine(p['start'].date() + datetime.timedelta(days=1),
                                       datetime.time(00, 00))
                '''
            p['start'] = dt.strftime(p['start'], '%Y%m%d%H%M%S') + ' +0900'
            p['stop'] = dt.strftime(p['stop'], '%Y%m%d%H%M%S') + ' +0900'
        return programs

    def parse_time(self, time_str, time_format='%H:%M'):
        return dt.strptime(time_str, time_format).time()

    def get_epg_info(self, raw_html, proc_date):
        programs = []
        for start_time, title in self.parse_epg_html(raw_html):
            start_time = self.parse_time(start_time)
            start_datetime = dt.combine(proc_date, start_time)
            programs.append({
                'start': start_datetime,
                'stop': '',
                'title': title,
            })
        return programs


class PriorityQueue(object):
    '''
    Not thread safe.
    '''

    entries = {}
    counter = itertools.count()

    def set(self, key, value, priority=0):
        self.entries[key] = [priority, next(self.counter), key, value]

    def get(self, key):
        priority, count, key, value = self.entries[key]
        #log.debug('---------- %d, %d, %s / %s', priority, count, key, self.entries)
        self.set(key, value, priority + 1)
        return value

    def except_get(self, excepts):
        names = [key for key in self.entries.keys() if key not in excepts]
        pq = []
        for key in names:
            heapq.heappush(pq, self.entries[key])
        priority, count, key, value = heapq.heappop(pq)
        #log.debug('---------- %d, %d, %s / %s', priority, count, key, self.entries)
        self.set(key, value, priority + 1)
        return key, value

    def size(self):
        return len(self.entries)

    def de_priority(self, key):
        self.set(key, self.entries[key][-1], self.entries[key][0] - 1)
