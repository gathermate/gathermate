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
    log.debug(pq.entries)

def set_epg(mapped_channel, days, pq):
    epg = dict(fails=[], programs=[], source=None)
    only = mapped_channel.get('only')
    skip = mapped_channel.get('skip')
    used = skip.split('|') if skip else []
    if only:
        with lock:
            grabber = pq.get(only)
        programs = grabber.get_epg(mapped_channel, days)
        if len(programs) > 0:
            epg['programs'].extend(programs)
            epg['source'] = grabber.__class__.__name__
        else:
            epg['fails'].append(grabber.__class__.__name__)
    else:
        while len(used) < pq.size():
            with lock:
                name, grabber = pq.except_get(used)
            used.append(name)
            if grabber.epg_search_type == 'id' and mapped_channel.get(name) is None:
                with lock:
                    pq.de_priority(name)
                continue
            programs = grabber.get_epg(mapped_channel, days)
            if len(programs) > 0:
                epg['programs'].extend(programs)
                epg['source'] = name
                break
            epg['fails'].append(name)
    mapped_channel['epg'] = epg
    return mapped_channel


class EpgGrabber(object):

    def __init__(self, fetcher):
        self.fetcher = fetcher

    def fetch(self, url, cached=False, **kwargs):
        return self.fetcher.fetch(url, cached=cached, **kwargs)

    def set_times(self, programs):
        programs = sorted(programs, key=lambda item: item.get('start'))
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
        return programs

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
