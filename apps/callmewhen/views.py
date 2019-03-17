# -*- coding: utf-8 -*-

import logging

from flask import Blueprint
from flask import request
from flask import current_app as app

from apps.common.cache import cache
from apps.common.auth import auth
from apps.common import urldealer as ud
from apps.common.datastructures import MultiDict

log = logging.getLogger(__name__)

name = 'Callmewhen'

cmw = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')

def make_cache_key():
    # type: () -> Text
    key = ud.Url(request.url).update_query(request.form).text if request.form else request.url
    return cache.create_key(key)

@cmw.route('/<string:order>', methods=['GET'])
@cache.cached(key_prefix=make_cache_key, timeout=cache.APP_TIMEOUT)
@auth.requires_auth
def send(order):
    # type: () -> Text
    query = MultiDict(request.args.iteritems(multi=True))
    return app.managers[name].request(order, query)