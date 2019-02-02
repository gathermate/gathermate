# -*- coding: utf-8 -*-

from flask import Blueprint
from flask import request
from flask import current_app as app

from apps.common.cache import cache
from apps.common.auth import auth
from apps.common import urldealer as ud

name = 'Telegram-bot'

telegram = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')

def make_cache_key():
    # type: () -> Text
    key = ud.URL(request.url).update_query(request.form).text if request.form else request.url
    return cache.create_key(key)

@telegram.route('/<string:order>', methods=['GET'])
@cache.cached(key_prefix=make_cache_key, timeout=cache.APP_TIMEOUT)
@auth.requires_auth
def send(order):
    # type: () -> Text
    args = request.args.copy()
    return app.managers[name].request(order, args)