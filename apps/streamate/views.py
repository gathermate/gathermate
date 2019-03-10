# -*- coding: utf-8 -*-

import logging
import json
from io import BytesIO

from flask import Blueprint
from flask import request
from flask import render_template
from flask import current_app as app
from flask import stream_with_context
from flask import Response
from flask import send_file

from apps.common.datastructures import MultiDict
from apps.common.exceptions import MyFlaskException
from apps.common.auth import auth


log = logging.getLogger(__name__)

name = 'Streamate'

streamate = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')


@streamate.route('/', strict_slashes=False)
@auth.requires_auth
def index():
    return render_template('player.html',
                           streamer=streamer)

@streamate.route('/<string:streamer>/resource')
def resource(streamer):
    query = MultiDict(request.args)
    return _order(streamer, 'resource', query)

@streamate.route('/<string:streamer>', strict_slashes=False)
@auth.requires_auth
def streamer(streamer):
    return render_template('player.html',
                           streamer=streamer)

@streamate.route('/<string:streamer>/channels')
@auth.requires_auth
def streamer_channels(streamer):
    query = MultiDict(request.args)
    channels, hasNext, page = _order(streamer, 'channels', query)
    return json.dumps(dict(channels=channels, hasNext=hasNext, page=page))

@streamate.route('/<string:streamer>/channels.m3u')
@auth.requires_auth
def streamer_channels_m3u(streamer):
    query = MultiDict(request.args)
    m3u_gen = _order(streamer, 'm3u', query)
    return Response(stream_with_context(m3u_gen), mimetype='application/x-mpegURL')

@streamate.route('/all-channels.m3u')
@auth.requires_auth
def m3u():
    query = MultiDict(request.args)
    m3u_gen = app.managers[name].order_all_m3u(query)
    return Response(stream_with_context(m3u_gen), mimetype='application/x-mpegURL')

@streamate.route('/<string:streamer>/<string:cid>/<string:order>')
@auth.requires_auth
def streamer_channel_info(streamer, cid, order):
    query = MultiDict(request.args)
    query['cid'] = cid
    return _order(streamer, order, query)

@streamate.route('/<string:streamer>/<string:cid>')
def streamer_channel_streaming(streamer, cid):
    qIndex = int(request.args.get('q', -1))
    gen = _order(streamer, 'streaming', None)
    return Response(stream_with_context(gen(cid, qIndex)), mimetype='video/MP2T')

def _order(streamer, order, query):
    return app.managers[name].request(streamer, order, query)
