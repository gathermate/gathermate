# -*- coding: utf-8 -*-
import urllib
import urlparse

SCHEME = 'scheme'
NETLOC = 'netloc'
PATH = 'path'
QUERY = 'query'
FRAGMENT = 'fragment'
USERNAME = 'username'
PASSWORD = 'password'
HOSTNAME = 'hostname'
PORT = 'port'


class URL(object):
    def __init__(self, url=''):
        # type: (str) -> None
        if url:
            self.url = split(url)

    @property
    def scheme(self):
        return self.url[SCHEME]

    @scheme.setter
    def scheme(self, v):
        self.url[SCHEME] = v

    @property
    def netloc(self):
        return self.url[NETLOC]

    @netloc.setter
    def netloc(self, v):
        self.url[NETLOC] = v

    @property
    def username(self):
        return self.url[USERNAME]

    @username.setter
    def username(self, v):
        self.url[USERNAME] = v

    @property
    def password(self):
        return self.url[PASSWORD]

    @password.setter
    def password(self, v):
        self.url[PASSWORD] = v

    @property
    def hostname(self):
        return self.url[HOSTNAME]

    @hostname.setter
    def hostname(self, v):
        self.url[HOSTNAME] = v

    @property
    def fragment(self):
        return self.url[FRAGMENT]

    @fragment.setter
    def fragment(self, v):
        self.url[FRAGMENT] = v

    @property
    def query_dict(self):
        return self.url[QUERY]

    @query_dict.setter
    def query_dict(self, v):
        self.url[QUERY] = v

    @property
    def path(self):
        return self.url[PATH]

    @path.setter
    def path(self, v):
        self.url[PATH] = v

    @property
    def query(self):
        # type: () -> str
        return unsplit_qs(self.url[QUERY])

    @query.setter
    def query(self, v):
        # type: (str) -> None
        self.url[QUERY] = split_qs(v)

    @property
    def port(self):
        # type: () -> int
        return int(self.url[PORT])

    @port.setter
    def port(self, v):
        # type: (int) -> None
        self.url[PORT] = v

    @property
    def text(self):
        # type: () -> str
        return unsplit_dict(self.url)

    @text.setter
    def text(self, v):
        # type: (str) -> None
        self.url = split(v)

    def update_query(self, post_dict):
        # type: (Dict[Text, Text]) -> None
        self.query_dict.update(post_dict)

    def update_qs(self, qs):
        # type: (str) -> None
        qs_dict = split_qs(qs)
        self.update_query(qs_dict)

    def __str__(self):
        # type: () -> str
        return self.text

    def get(self, key):
        # type: (str) -> Union[Text, None]
        return self.url.get(key, None)

def unquote(qs):
    # type: (str) -> str
    return urllib.unquote(qs)

def quote(qs):
    # type: (Text) -> str
    if isinstance(qs, unicode):
        qs = qs.encode('utf-8', 'ignore')
    return urllib.quote(qs)

def join_qs(old, new):
    # type: (str, str) -> str
    old_dict = split_qs(old)
    old_dict.update(split_qs(new))
    return unsplit_qs(old_dict)

def join(old, new):
    # type: (str, str) -> str
    return urlparse.urljoin(old, new)

def split_qs(qs):
    # type: (str) -> Dict[Text, list]]
    if not qs:
        return {}
    return urlparse.parse_qs(qs, keep_blank_values=True)

def unsplit_qs(qs_dict):
    # type: (Dict[Text, list]) -> str
    if not qs_dict:
        return ''
    sorted_query = sorted(
        (pair for pair in qs_dict.items())
    )
    qs = urllib.urlencode(sorted_query, True)
    return qs

def remove_qs(qs, key):
    # type: (str, str) -> str
    qs_dict = split_qs(qs)
    qs_dict.pop(key)
    return unsplit_qs(qs_dict)

def split(url):
    # type: (str) -> Dict[Text, Text]
    parsed = urlparse.urlsplit(url, scheme='http')
    url_dict = {
        SCHEME: parsed.scheme,
        NETLOC: parsed.netloc if parsed.netloc else parsed.path,
        QUERY: split_qs(parsed.query),
        FRAGMENT: parsed.fragment,
        USERNAME: parsed.username,
        PASSWORD: parsed.password,
        HOSTNAME: parsed.hostname,
        PORT: parsed.port,
    }
    url_dict[PATH] = parsed.path if not url_dict[NETLOC] == parsed.path else ''
    return url_dict

def unsplit_dict(url_dict):
    # type: (Dict[Text, Text]) -> str
    # <scheme>://<username>:<password>@<host>:<port>/<path>;<parameters>?<query>#<fragment>
    # urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
    query = unsplit_qs(url_dict[QUERY])
    url = urlparse.urlunsplit((url_dict.get(SCHEME),
                               url_dict.get(NETLOC),
                               url_dict.get(PATH),
                               query,
                               url_dict.get(FRAGMENT)))
    return url

def unsplit(url_tuple):
    # type: (Tuple[Text]) -> Dict[Text, Text]
    url_dict = {
        SCHEME: url_tuple[0],
        NETLOC: url_tuple[1],
        PATH: url_tuple[2],
        QUERY: split_qs(url_tuple[3]),
        FRAGMENT: url_tuple[4],
    }
    return unsplit_dict(url_dict)
