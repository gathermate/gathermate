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
    query = MultiDict(request.args.iteritems(multi=True))
    return _order(streamer, 'resource', query)

@streamate.route('/<string:streamer>', strict_slashes=False)
@auth.requires_auth
def streamer(streamer):
    return render_template('player.html',
                           streamer=streamer)

@streamate.route('/<string:streamer>/channels')
@auth.requires_auth
def streamer_channels(streamer):
    query = MultiDict(request.args.iteritems(multi=True))
    def gen():
        counter = 1
        for ch in _order(streamer, 'channels', query):
            if ch.exclusive:
                info = "dict(cid='%s', chnum='%d', tving='%s', logo='%s', name='%s')," % (
                    ch.name[0] + str(counter), counter, ch.cid, ch.logo, ch.name)
                yield info + '\n'
            counter += 1
    return Response(stream_with_context(gen()), mimetype='text/plain')

@streamate.route('/<string:streamer>/m3u')
@auth.requires_auth
def streamer_m3u(streamer):
    query = MultiDict(request.args.iteritems(multi=True))
    m3u_gen = _order(streamer, 'm3u', query)
    response = Response(stream_with_context(m3u_gen), mimetype='application/x-mpegURL')
    response.headers['Content-Disposition'] = 'attachment; filename={}.m3u'.format(streamer)
    return response

@streamate.route('/<string:streamer>/epg')
@auth.requires_auth
def streamer_epg(streamer):
    query = MultiDict(request.args.iteritems(multi=True))
    epg_gen = _order(streamer, 'epg', query)
    return Response(stream_with_context(epg_gen), mimetype='text/xml')

@streamate.route('/m3u')
@auth.requires_auth
def m3u():
    query = MultiDict(request.args.iteritems(multi=True))
    m3u_gen = app.managers[name].order_all_m3u(query)
    response = Response(stream_with_context(m3u_gen), mimetype='application/x-mpegURL')
    response.headers['Content-Disposition'] = 'attachment; filename=all.m3u'
    return response

@streamate.route('/epg')
@auth.requires_auth
def epg():
    query = MultiDict(request.args.iteritems(multi=True))
    epg_gen = app.managers[name].order_all_epg(query)
    response = Response(stream_with_context(epg_gen), mimetype='text/xml')
    response.headers['Content-Disposition'] = 'attachment; filename=all.xml'
    return response

@streamate.route('/<string:streamer>/<string:cid>/<string:order>')
@auth.requires_auth
def streamer_channel_info(streamer, cid, order):
    query = MultiDict(request.args.iteritems(multi=True))
    query['cid'] = cid
    return _order(streamer, order, query)

@streamate.route('/<string:streamer>/<string:cid>')
@auth.requires_auth
def streamer_channel_streaming(streamer, cid):
    qIndex = int(request.args.get('q', -1))
    gen = _order(streamer, 'streaming', None)
    response = Response(stream_with_context(gen(cid, qIndex)), mimetype='video/MP2T')
    response.headers['Content-Disposition'] = 'attachment; filename={}-{}.ts'.format(streamer, cid)
    return response

def _order(streamer, order, query):
    return app.managers[name].request(streamer, order, query)