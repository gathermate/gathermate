# -*- coding: utf-8 -*-

import logging

from flask import Blueprint
from flask import request
from flask import current_app as app
from flask import stream_with_context
from flask import Response

from apps.common.auth import auth
from apps.common import caching

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
    return 'Welcome'

@streamate.route('/<path:streamer>/resource')
def resource(streamer):
    return _order(streamer, 'resource', request.args)

@streamate.route('/<path:streamer>', strict_slashes=False)
@auth.requires_auth
def streamer(streamer):
    return streamer

@streamate.route('/<path:streamer>/<string:cid>')
def streamer_channel_streaming(streamer, cid):
    qIndex = request.args.get('q', -1, int)
    gen = _order(streamer, 'streaming', None)
    response = Response(stream_with_context(gen(cid, qIndex)), mimetype='video/MP2T')
    response.headers['Content-Disposition'] = 'attachment; filename={}-{}.ts'.format(streamer, cid)
    return response

@streamate.route('/<path:streamer>/channels')
@auth.requires_auth
def streamer_channels(streamer):
    return Response(stream_with_context(_order(streamer, 'channels', request.args)), mimetype='text/plain')

@streamate.route('/<path:streamer>/<string:filename>.m3u')
@auth.requires_auth
def streamer_m3u(streamer, filename):
    gen = _order(streamer, 'm3u', request.args)
    return _get_m3u_response(gen, filename)

@streamate.route('/<string:filename>.m3u')
@auth.requires_auth
def m3u(filename):
    gen = app.managers[name].order_all_m3u(request.args)
    return _get_m3u_response(gen, filename)

@streamate.route('/<string:filename>.xml')
@auth.requires_auth
def epg(filename):
    gen = app.managers[name].order_all_epg(request.args)
    return _get_epg_response(gen, filename)

def _order(streamer, order, query):
    return app.managers[name].request(streamer, order, query)

def _get_m3u_response(generator, filename):
    response = Response(stream_with_context(generator), mimetype='application/x-mpegURL')
    response.headers['Content-Disposition'] = 'attachment; filename={}.m3u'.format(filename)
    return response

def _get_epg_response(generator, filename):
    response = Response(stream_with_context(generator), mimetype='application/xml')
    response.headers['Content-Disposition'] = 'attachment; filename={}.xml'.format(filename)
    return response
