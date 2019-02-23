# -*- coding: utf-8 -*-

import os

class Flask(object):
    SECRET_KEY = os.urandom(8).encode('hex')
    LOG_LEVEL = 'DEBUG'
    NOTIFY = False
    TELEGRAM_BOT_TOKEN = ''
    TELEGRAM_CHAT_ID = 123456789
    MANAGERS = {
        'Scrapmate': 'apps.scrapmate.manager',
        'Callmewhen': 'apps.callmewhen.manager',
    }
    BLUEPRINTS = {
        'Scrapmate': {
            'module': 'apps.scrapmate.views',
            'instance': 'scrapmate',
            'url_prefix': '/scrap',
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
    ACCEPTED_EXT = ['.torrent', '.smi', '.srt',]
    FETCHER = {
        'CACHE_TIMEOUT': 60,
        'DEADLINE': 60,
        'COOKIE_FILE': False,
        'COOKIE_PATH': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cookies'),
        'COOKIE_TIMEOUT' : 0,
    }
    SCRAPERS = {}
    POOQ = {}
    TVING = {}

class GoogleAppEngine(Localhost):
    NAME = 'GoogleAppEngine @ default'
