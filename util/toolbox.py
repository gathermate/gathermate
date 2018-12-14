# -*- coding: utf-8 -*-

import time
import threading
import os
import re
import io
import json
import chardet
import logging as log
import csv
import codecs
import cStringIO
from difflib import SequenceMatcher
from functools import wraps
import inspect

def timeit(method):
    # type: (Callable[..., ...]) -> Callable[List[object], Dict[object, object], object]
    @wraps(method)
    def timed(*args, **kw):
        #print '%r starts on %s' % (method.__name__, threading.current_thread())
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            log.debug('{:s}() takes {:,.2f} ms on {:s}'.format(method.__name__, (te - ts) * 1000, threading.current_thread()))
        return result
    return timed

@timeit
def decode(content):
    # type: (str) -> unicode
    if content is None:
        log.warning('There is no string to decode.')
        return content
    encoding = chardet.detect(content)['encoding']
    if encoding is None:
        log.warning('Could not figure out what encoding is.')
        return content

    result = content.decode(encoding)
    stack = inspect.stack()[2]
    log.debug('[{0:s}()] decodes [{1:s}] string from [{2:s}:{3:d}]]'.format(stack[3], encoding, stack[1], stack[2]))

    return result

MIME = {
        '.torrent': 'application/x-bittorrent',
        '.jpg': 'image/jpeg',
        '.gif': 'image/gif',
        '.png': 'image/png',
        '.smi': 'application/smil+xml',
        '.srt': 'application/x-subrip',
}
def get_mime(filename):
    # type: (str) -> str
    ext = get_ext(filename)[1]
    ext = '.jpg' if ext in ['.jpg', '.jpeg'] else ext
    try:
        return MIME[ext]
    except KeyError:
        return 'application/octet-stream'

def get_ext(filename):
    # type: (str) -> Tuple(str, str)
    name, ext = os.path.splitext(filename.lower())
    return name, ext

def tell_type(obj):
    # type: (Type[object]) -> None
    string = '##### type of {} is {} #####'.format(obj, type(obj))
    print(string)
    log.debug(string)

# https://usamaejaz.com/cloudflare-email-decoding/
def cf_decode(encodedString):
    r = int(encodedString[:2],16)
    text = ''.join([chr(int(encodedString[i:i+2], 16) ^ r) for i in range(2, len(encodedString), 2)])
    return text

REGEXP_FILENAME = re.compile(r'filename[^;\n=]*=([\'\"])*(.*)(?(1)\1|)')
def filename_from_headers(headers):
    # type: (Dict[str, str]) -> unicode

    #regex = r'filename[^;\n=]*=([\'\"])*(.*)(?(1)\1|)'
    target = headers.get('Content-Disposition')
    target = decode(target)
    filename = REGEXP_FILENAME.search(target, re.I).group(2)
    return filename

def compare(a, b):
    # Type: (Text, Text) -> float
    return SequenceMatcher(None, a, b).ratio()

def dict_from_json_file(self, file):
    # type: (str) -> Union[Dict[object, object], None]
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception as e:
        log.error(e)

def dict_to_json_file(self, _dict, file):
    # type: (Dict[object, object], str) -> None
    with open(file, 'w') as f:
        f.write(json.dumps(_dict))

def read_M3U(m3u_file):
    # type: (str) -> List[Dict[str, Union[str, int]]]
    _list = []
    with io.open(m3u_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    ext = lines.pop(0).strip()
    if not ext == '#EXTM3U':
        log.error('#EXTM3U missing.')
        return
    for num in range(0, len(lines), 2):
        _dict = {}
        attributes, title = lines[num].split('#EXTINF:')[1].split(',')
        _dict['title'] = title.strip()
        attrs = attributes.split(' ')
        duration = attrs.pop(0)
        _dict['duration'] = int(duration)
        for a in attrs:
            key, value = a.split('=')
            value = value.strip('\'"')
            try:
                _dict[key] = int(value)
            except ValueError:
                _dict[key] = value
        _dict['media'] = lines[num + 1].strip()

        _list.append(_dict)

    return _list

def read_CSV(csv_file):
    # type: (str) -> List[Dict[str, str]]
    _list = []
    with open(csv_file, 'r') as f:
        ur = UnicodeReader(f, encoding='utf-8')
        _key = ur.next()
        for line in ur:
            _dict = {}
            for i in range(0, len(_key)):
                _dict.update({_key[i]: line[i]})
            _list.append(_dict)
    return _list

def write_M3U(m3u, file):
    # type: (str, str) -> None
    with io.open(file, 'w', encoding='utf-8') as f:
        f.write(u'#EXTM3U\n')
        for mux in m3u:
            duration = mux.pop('duration')
            title = mux.pop('title')
            media = mux.pop('media').strip()
            attr = []
            for k, v in mux.items():
                attr.append(u'{}="{}"'.format(k, v))
            attrs = ' '.join(attr)
            line = u'#EXTINF:{:d} {:s},{:s}\n{:s}\n'.format(duration, attrs, title, media)
            f.write(line)

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')