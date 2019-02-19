# -*- coding: utf-8 -*-

import logging

from flask import Blueprint
from flask import request
from flask import render_template
from flask import current_app as app

from apps.common.datastructures import MultiDict
from apps.common.exceptions import MyFlaskException

log = logging.getLogger(__name__)

name = 'Streamate'

streamate = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')

@streamate.route('/', strict_slashes=False)
def index():
    return 'Streamate'

@streamate.route('/server/<string:fname>')
def serve(fname):
    return streamate.send_static_file('./video/%s' % fname)

@streamate.route('/<string:streamer>')
def streamer(streamer):
    query = MultiDict(request.args)
    if 'resource' in query:
        if query.get('resource') == '': return 'Empty'
        r = app.managers[name].request(streamer, 'resource', query)
        return (r.content, r.status_code, dict(r.headers))
    else:
        channels = app.managers[name].request(streamer, 'channels', query)
        return render_template('player.html',
                               streamer=streamer,
                               channels=channels)

@streamate.route('/<path:streamer>/<path:cid>')
def channel(streamer, cid):
    query = MultiDict(request.args)
    query['cid'] = cid
    if 'media' in query:
        order = 'media'
    elif 'list' in query:
        order = 'playlist'
    else:
        order = 'streamlist'
    r = app.managers[name].request(streamer, order, query)
    return (r.content, r.status_code, dict(r.headers))

@streamate.errorhandler(Exception)
def unhandled_exception(e):
    # type: (Type[Exception]) -> Text
    MyFlaskException.trace_error()
    return e.message