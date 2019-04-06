# -*- coding: utf-8 -*-

import logging
import os
from functools import wraps

from flask_caching import Cache
from flask import request

log = logging.getLogger(__name__)

cache = Cache()
config = {}

def create_key(key):
    return '{}-{}'.format(config.get('SECRET_KEY', os.urandom(8).encode('hex')), key)

def init(app, app_config, cache_type):
    global config
    config = app_config
    cache.init_app(app, config=cache_type)
    cache.clear()
