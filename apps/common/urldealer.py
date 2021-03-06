# -*- coding: utf-8 -*-
import urllib
import urlparse
import logging

from tld import get_fld

from apps.common.datastructures import MultiDict

SCHEME = 'scheme'
NETLOC = 'netloc'
PATH = 'path'
QUERY = 'query'
FRAGMENT = 'fragment'
USERNAME = 'username'
PASSWORD = 'password'
HOSTNAME = 'hostname'
DOMAIN = 'domain'
PORT = 'port'


class Url(object):
    def __init__(self, url=''):
        if url:
            self.url = split(url)

    @property
    def scheme(self):
        return self.url[SCHEME]

    @scheme.setter
    def scheme(self, v):
        self.url[SCHEME] = v
        return self

    @property
    def netloc(self):
        return self.url[NETLOC]

    @netloc.setter
    def netloc(self, v):
        self.url[NETLOC] = v
        return self

    @property
    def username(self):
        return self.url[USERNAME]

    @username.setter
    def username(self, v):
        self.url[USERNAME] = v
        return self

    @property
    def password(self):
        return self.url[PASSWORD]

    @password.setter
    def password(self, v):
        self.url[PASSWORD] = v
        return self

    @property
    def hostname(self):
        return self.url[HOSTNAME]

    @hostname.setter
    def hostname(self, v):
        self.url[HOSTNAME] = v
        return self

    @property
    def domain(self):
        return self.url[DOMAIN]

    @property
    def fragment(self):
        return self.url[FRAGMENT]

    @fragment.setter
    def fragment(self, v):
        self.url[FRAGMENT] = v
        return self

    @property
    def query_dict(self):
        return self.url[QUERY]

    @query_dict.setter
    def query_dict(self, v):
        self.url[QUERY] = v
        return self

    @property
    def path(self):
        return self.url[PATH]

    @path.setter
    def path(self, v):
        self.url[PATH] = v
        return self

    @property
    def full_path(self):
        return '?'.join([self.path, self.query])

    @property
    def query(self):
        return unsplit_qs(self.url[QUERY])

    @query.setter
    def query(self, v):
        self.url[QUERY] = split_qs(v)
        return self

    @property
    def port(self):
        return int(self.url[PORT])

    @port.setter
    def port(self, v):
        self.url[PORT] = v
        return self

    @property
    def text(self):
        return unsplit(self.url)

    @text.setter
    def text(self, v):
        self.url = split(v)
        return self

    def update_query(self, post_dict):
        for _tuple in post_dict.iteritems():
            self.query_dict.poplist(_tuple[0])
        self.query_dict.update(post_dict)
        return self

    def update_qs(self, qs):
        qs_dict = split_qs(qs)
        self.update_query(qs_dict)
        return self

    def __str__(self):
        return self.text

    def __repr__(self):
        return '<{}.{} \'{}\'>'.format(self.__module__,
                                       self.__class__.__name__,
                                       self.text)

    def get(self, key):
        return self.url.get(key, None)

def unquote(qs):
    return urllib.unquote_plus(qs)

def quote(qs):
    if isinstance(qs, unicode):
        qs = qs.encode('utf-8', 'ignore')
    return urllib.quote_plus(qs)

def join_qs(old, new):
    old_dict = split_qs(old)
    old_dict.update(split_qs(new))
    return unsplit_qs(old_dict)

def join(old, new):
    return urlparse.urljoin(old, new)

def split_qs(qs):
    return MultiDict(urlparse.parse_qs(qs, keep_blank_values=True))

def unsplit_qs(qs_dict):
    if not qs_dict:
        return ''
    sorted_query = sorted(
        (pair for pair in qs_dict.iteritems())
    )
    qs = urllib.urlencode(sorted_query, True)
    return qs

def remove_qs(qs, key):
    qs_dict = split_qs(qs)
    qs_dict.pop(key)
    return unsplit_qs(qs_dict)

def split(url):
    parsed = urlparse.urlsplit(str(url), scheme='http')
    url_dict = {
        SCHEME: parsed.scheme,
        NETLOC: parsed.netloc if parsed.netloc else parsed.path,
        QUERY: split_qs(parsed.query),
        FRAGMENT: parsed.fragment,
        USERNAME: parsed.username,
        PASSWORD: parsed.password,
        HOSTNAME: parsed.hostname,
        PORT: parsed.port,
        DOMAIN: get_domain(url),
    }
    url_dict[PATH] = parsed.path if not url_dict[NETLOC] == parsed.path else ''
    return url_dict

def unsplit(url_dict):
    query = unsplit_qs(url_dict[QUERY])
    netloc = url_dict.get(NETLOC)
    if url_dict.get(USERNAME) and url_dict.get(PASSWORD):
        netloc = '{}:{}@{}'.format(url_dict.get(USERNAME), url_dict.get(PASSWORD), url_dict.get(NETLOC))
    url = urlparse.urlunsplit((url_dict.get(SCHEME),
                               netloc,
                               url_dict.get(PATH),
                               query,
                               url_dict.get(FRAGMENT)))
    return url

def get_domain(url):
    return get_fld(url, fix_protocol=True, fail_silently=True)
