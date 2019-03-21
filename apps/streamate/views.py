# -*- coding: utf-8 -*-

import logging
from datetime import datetime as dt

from flask import Blueprint
from flask import request
from flask import render_template
from flask import current_app as app
from flask import stream_with_context
from flask import Response

from apps.common.datastructures import MultiDict
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
    return 'Welcome'
    return render_template('player.html',
                           streamer=streamer)

@streamate.route('/<path:streamer>/resource')
def resource(streamer):
    query = MultiDict(request.args.iteritems(multi=True))
    return _order(streamer, 'resource', query)

@streamate.route('/<path:streamer>', strict_slashes=False)
@auth.requires_auth
def streamer(streamer):
    return streamer
    return render_template('player.html',
                           streamer=streamer)

@streamate.route('/<path:streamer>/<string:cid>')
@auth.requires_auth
def streamer_channel_streaming(streamer, cid):
    qIndex = int(request.args.get('q', -1))
    gen = _order(streamer, 'streaming', None)
    response = Response(stream_with_context(gen(cid, qIndex)), mimetype='video/MP2T')
    response.headers['Content-Disposition'] = 'attachment; filename={}-{}.ts'.format(streamer, cid)
    return response

@streamate.route('/<path:streamer>/channels')
@auth.requires_auth
def streamer_channels(streamer):
    query = MultiDict(request.args.iteritems(multi=True))
    def gen():
        for ch in _order(streamer, 'channels', query):
            info = "dict(cid='', chnum='', %s='%s', logo='%s', name='%s')," % (
                streamer, ch.cid, ch.logo, ch.name)
            yield info + '\n'
    return Response(stream_with_context(gen()), mimetype='text/plain')

@streamate.route('/<path:streamer>/<string:filename>.m3u')
@auth.requires_auth
def streamer_m3u(streamer, filename):
    query = MultiDict(request.args.iteritems(multi=True))
    m3u_gen = _order(streamer, 'm3u', query)
    response = Response(stream_with_context(m3u_gen), mimetype='application/x-mpegURL')
    response.headers['Content-Disposition'] = 'attachment; filename={}.m3u'.format(filename)
    return response

@streamate.route('/<string:filename>.m3u')
@auth.requires_auth
def m3u(filename):
    query = MultiDict(request.args.iteritems(multi=True))
    m3u_gen = app.managers[name].order_all_m3u(query)
    response = Response(stream_with_context(m3u_gen), mimetype='application/x-mpegURL')
    response.headers['Content-Disposition'] = 'attachment; filename={}.m3u'.format(filename)
    return response

@streamate.route('/<string:filename>.xml')
@auth.requires_auth
def epg(filename):
    query = MultiDict(request.args.iteritems(multi=True))
    epg_gen = app.managers[name].order_all_epg(query)
    response = Response(stream_with_context(epg_gen), mimetype='application/xml')
    response.headers['Content-Disposition'] = 'attachment; filename={}.xml'.format(filename)
    return response

def _order(streamer, order, query):
    return app.managers[name].request(streamer, order, query)
