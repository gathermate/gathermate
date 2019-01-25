# -*- coding: utf-8 -*-

import os

class Flask(object):
    SECRET_KEY = os.urandom(32).encode('hex')
    LOG_LEVEL = 'DEBUG'
    MANAGERS = {
        'Gathermate': 'apps.gathermate.manager',
    }
    BLUEPRINTS = {
        'Gathermate': {
            'module': 'apps.gathermate.views',
            'instance': 'gathermate',
            'url_prefix': '/gather',
        },
    }

class Localhost(Flask):
    NAME = 'Localhost @ default'
    TIMEOUT = 5
    AUTH_ID = os.environ.get('GATHERMATE_AUTH_ID', None)
    AUTH_PW = os.environ.get('GATHERMATE_AUTH_PW', None)
    RSS_AGGRESSIVE = False
    RSS_ASYNC = False
    RSS_WORKERS = 5
    RSS_LENGTH = 5
    RSS_WANT = ['1080(?i)P', '(?i)bluray']
    ACCEPTED_EXT = ['.torrent', '.smi', '.srt', '.zip', '.rar']
    FETCHER = {
        'CACHE_TIMEOUT': 60,
        'COOKIE_TIMEOUT': 3600,
        'DEADLINE': 60,
    }
    GATHERERS = {
        'Etoland': {
            'ENCODING': 'euc-kr',
            'mb_id': os.environ.get('GATHERMATE_ETO_ID', None),
            'mb_password': os.environ.get('GATHERMATE_ETO_PW', None),
        },
        'Cineaste': {
            'mb_id': os.environ.get('GATHERMATE_CINE_ID', None),
            'mb_password': os.environ.get('GATHERMATE_CINE_PW', None),
        },
    }


class GoogleAppEngine(Localhost):
    NAME = 'GoogleAppEngine @ default'
