# -*- coding: utf-8 -*-

import logging

from flask import Blueprint
from flask import request
from flask import render_template
from flask import current_app as app

from apps.common.datastructures import MultiDict
from apps.common.exceptions import MyFlaskException
from apps.common.fetchers import Response as Rspns

log = logging.getLogger(__name__)

name = 'Streamate'

streamate = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')

@streamate.route('/', strict_slashes=False)
def index():
    return render_template('player.html',
                           streamer=streamer)

@streamate.route('/<string:streamer>/resource')
def resource(streamer):
    query = MultiDict(request.args)
    return _order(streamer, 'resource', query)

@streamate.route('/<string:streamer>', strict_slashes=False)
def streamer(streamer):
    query = MultiDict(request.args)
    channels = _order(streamer, 'channels', query)
    return render_template('player.html',
                           streamer=streamer,
                           channels=channels)

@streamate.route('/<path:streamer>/<path:cid>/<path:order>')
def channel(streamer, cid, order):
    query = MultiDict(request.args)
    query['cid'] = cid
    return _order(streamer, order, query)

def _order(streamer, order, query):
    return app.managers[name].request(streamer, order, query)

@streamate.errorhandler(Exception)
def unhandled_exception(e):
    # type: (Type[Exception]) -> Text
    MyFlaskException.trace_error()
    return e.message, 404