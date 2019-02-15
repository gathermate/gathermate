# -*- coding: utf-8 -*-

import logging as log
import json

from flask import Blueprint
from flask import request
from flask import send_from_directory
from flask import make_response
from flask import stream_with_context
from flask import render_template
from flask import current_app as app

from apps.common import urldealer as ud
from apps.common import fetchers
from apps.common.datastructures import MultiDict

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


# /stream/pooq
# /stream/pooq/vod/
# /stream/pooq/resource/
# /stream/pooq/live/ -> api/live/all-channels
# /stream/pooq/live/epgs -> epg
# /stream/pooq/live/K01 -> api/live/channels/K01
# /stream/pooq/live/K01/epgs -> channel epg
# /stream/pooq/live/K01/480p/1234567.ts


@streamate.route('/<path:streamer>')
def streamer(streamer):
    query = MultiDict(request.args)
    if query.get('resource', False):
        r = app.managers[name].request(streamer, query)
        response = make_response(r.content)
        response.headers = dict(r.headers)
        response.status_code = r.status_code
        return response
    else:
        query['channel'] = 'all'
        data = app.managers[name].request(streamer, query)
        return render_template('player2.html',
                               streamer=streamer,
                               data=data)

@streamate.route('/<path:streamer>/live/<path:channel>')
def channel(streamer, channel):
    query = MultiDict(request.args)
    query['channel'] = channel
    data = app.managers[name].request(streamer, query)
    response = make_response(data)
    if data.startswith('#EXTM3U'):
        response.headers["Content-Disposition"] = "attachment; filename=%s.m3u8" % streamer
        response.headers["Content-type"] = "application/vnd.apple.mpegurl"
    return response
