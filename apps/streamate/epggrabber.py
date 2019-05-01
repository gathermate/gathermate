# -*- coding: utf-8 -*-

import datetime
from datetime import datetime as dt
import logging
import heapq
import itertools
import threading

from concurrent import futures

from apps.common.datastructures import MultiDict

log = logging.getLogger()
lock = threading.RLock()

def get_epg(channel_map, grabbers, days=1):
    pq = PriorityQueue()
    for grabber in grabbers:
        grabber.gcounter = 0
        pq.set(grabber.__class__.__name__.lower(), grabber)
    with futures.ThreadPoolExecutor() as exe:
        fs = [exe.submit(set_epg, cid, ch, days, pq) for cid, ch in channel_map.iteritems()]
        try:
            for f in futures.as_completed(fs, timeout=30):
                yield f.result()
        except Exception as e:
            log.error(e.message)
    log.debug('\n' + '\n'.join(['%s : priority(%d), age(%d)' % (n.upper(), p, c) for p, c, n, _ in pq.entries.values()]) + '\n')

def set_epg(cid, mapped_channel, days, pq):
    mapped_channel['cid'] = cid
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
                log.warning('%s is required to grab %s', ke.message.capitalize(), mapped_channel['name'])
                return mapped_channel
            epg['programs'] = grabber.get_epg(mapped_channel, days)
            if epg['programs']: break
            epg['fails'].append(grabber.__class__.__name__)
    else:
        while len(skip) < pq.size():
            with lock:
                name, grabber = pq.except_get(skip)
            skip.append(name)
            if grabber.id_required and mapped_channel.get(name) is None:
                with lock: pq.de_priority(name)
                continue
            epg['programs'] = grabber.get_epg(mapped_channel, days)
            if epg['programs']: break
            epg['fails'].append(name)
    if epg['programs']:
        epg['source'] = grabber.__class__.__name__
    return mapped_channel


class EpgGrabber(object):

    id_required = True

    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.search_count = 0
        self.fail_count = 0

    def get_programs(self):
        raise NotImplementedError

    def fetch(self, url, cached=False, **kwargs):
        return self.fetcher.fetch(url, cached=cached, **kwargs)

    def get_epg(self, mapped_channel, days=1):
        if self.id_required:
            id_ = self.check_id(mapped_channel, self.__class__.__name__.lower())
            if id_ is False: return []
        self.search_count += 1
        programs = self.get_programs(mapped_channel, dt.today(), days)
        if not programs:
            log.warning("%s couldn't get EPG for the channel : %s", self.__class__.__name__, mapped_channel.get('name'))
            self.fail_count += 1
        return programs

    def set_stop(self, programs, last_duration=3):
        programs = sorted(programs, key=lambda p: p.start)
        for idx, p in enumerate(programs):
            if idx + 1 < len(programs):
                p['stop'] = programs[idx + 1].start
            else:
                # give 3 hours to the last program duration.
                p['stop'] = p.start + datetime.timedelta(hours=last_duration)
        return programs

    def parse_time(self, time_str, time_format='%H:%M'):
        return dt.strptime(time_str, time_format).time()

    def check_id(self, mapped_channel, key):
        ch_id = mapped_channel.get(key)
        if ch_id is None:
            log.warning("%s doesn't have ID for this channel : %s", self.__class__.__name__, mapped_channel.get('name'))
            return False
        return ch_id


class Program(MultiDict):

    @property
    def cid(self):
        return self.get('cid')

    @property
    def title(self):
        return self.get('title')

    @property
    def sub_title(self):
        return self.get('sub_title')

    @property
    def start(self):
        return self.get('start')

    @property
    def starts(self):
        return dt.strftime(self.get('start'), '%Y%m%d%H%M%S') + ' +0900'

    @property
    def stop(self):
        return self.get('stop')

    @property
    def stops(self):
        return dt.strftime(self.get('stop'), '%Y%m%d%H%M%S') + ' +0900'

    @property
    def description(self):
        return self.get('description')

    @property
    def category(self):
        return self.get('category')

    @property
    def rating(self):
        return self.get('rating')

    @property
    def episode(self):
        return self.get('episode')

    @property
    def rerun(self):
        return self.get('rerun')


class PriorityQueue(object):
    '''
    Not thread safe.
    '''
    def __init__(self):
        self.entries = {}
        self.counter = itertools.count()

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
