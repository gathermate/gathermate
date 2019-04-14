# -*- coding: utf-8 -*-

import logging
import inspect
from functools import wraps

from flask import request

from apps.common import caching

log = logging.getLogger(__name__)

def extract_query(*query):
    def wrapper(func):
        @wraps(func)
        def extract(*args, **kwargs):
            for q in query:
                if request.args.get(q) is not None:
                    if len(request.args.getlist(q)) > 2:
                        kwargs[q] = request.args.getlist(q)
                    else:
                        kwargs[q] = request.args.get(q)
            return func(*args, **kwargs)
        return extract
    return wrapper

def check_error(func):
    @wraps(func)
    def check_cache(*args, **kwargs):
        error = caching.cache.get(caching.make_view_error_key())
        if error is not None:
            log.error('Cached error : ' + error.message)
            return 'This request raised error before, try later.'
        else:
            return func(*args, **kwargs)
    return check_cache

def check_error_by_parameter(app_name):
    def wrapper(func):
        @wraps(func)
        def check_cache(*args, **kwargs):
            parameter_names, varargs, keywords, defaults = inspect.getargspec(func)
            kw_list = []
            for name in parameter_names:
                if name in kwargs:
                    if name is 'self':
                        kw_list.append(kwargs[name].__class__.__name__.lower())
                    else:
                        kw_list.append(kwargs[name])
                else:
                    kw_list.append(defaults[parameter_names.index(name)-len(parameter_names)])
            key = caching.make_error_key([app_name] + list(args) + kw_list)
            error = caching.cache.get(key)
            if error is not None:
                log.error('Cached error : ' + error.message)
                return 'This request raised error before, try later.', 404
            else:
                return func(*args, **kwargs)
        return check_cache
    return wrapper
