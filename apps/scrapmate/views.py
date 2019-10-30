# -*- coding: utf-8 -*-

import logging
from io import BytesIO

from flask import Blueprint
from flask import render_template
from flask import send_file
from flask import request
from flask import Response
from flask import current_app as app
from flask import redirect
from flask import render_template_string
from flask import flash
from flask import stream_with_context

from apps.common.auth import auth
from apps.common.exceptions import GathermateException

log = logging.getLogger()
name = 'Scrapmate'
scrapmate = Blueprint(name, __name__)

@scrapmate.route('/', strict_slashes=False)
@auth.requires_auth
def index():
    return render_template('scrapmate/index.html')

@scrapmate.route('/encode', methods=['GET'])
@auth.requires_auth
def quote():
    return render_template('scrapmate/encode.html')

@scrapmate.route('/<path:site>/<path:board>/rss', methods=['GET'])
@auth.requires_auth
def rss_by_alias(site, board):
    request.args['site'] = site
    request.args['board'] = board
    data = app.managers[name].request_board('rss', request.args)
    return order_rss(data)

@scrapmate.route('/<path:site>/<path:board>', methods=['GET'])
@auth.requires_auth
def list_by_alias(site, board):
    request.args['site'] = site
    request.args['board'] = board
    data = app.managers[name].request_board('list', request.args)
    return order_list(data)

@scrapmate.route('/<path:site>/custom', methods=['GET'])
@auth.requires_auth
def custom_by_alias(site):
  request.args['site'] = site
  data = app.managers[name].request_board('custom', request.args)
  if data is None:
    return "No data returned."
  return Response(stream_with_context(data), mimetype='text/plain')

@scrapmate.route('/<path:order>', methods=['GET'])
@auth.requires_auth
def order(order):
    ''' Do not name order()'s args with query names ex) path, netloc, scheme etc... '''
    data = app.managers[name].request_board(order, request.args)
    return globals()['order_{}'.format(order)](data)

def order_rss(generator):
    return Response(stream_with_context(generator), mimetype='text/xml')

def order_down(data):
    try:
        return send_file(BytesIO(data.content),
                         as_attachment=True,
                         mimetype=data.headers['content-type'],
                         attachment_filename=data.filename)
    except AttributeError:
        return redirect(data)

def order_list(data):
    pagination = Pagination(data['current_page'], data['max_page'])
    return render_template('scrapmate/list.html',
                           index=request.args.get('index'),
                           pagination=pagination,
                           title='Scrapmate',
                           search=request.args.get('search'),
                           articles=data['articles'])

def order_item(data):
    return render_template('scrapmate/view.html', items=data)

def order_page(data):
    return data

@scrapmate.errorhandler(Exception)
@auth.requires_auth
def unhandled_exception(e):
    GathermateException.trace_error()
    if hasattr(e, 'message') and e.message != '':
        err_message = e.message
    else:
        err_message = str(e)
    flash(err_message)
    app.send('{}#{}'.format(name, request.host), err_message)
    path = request.path.split('/')
    content = None
    if type(e) is GathermateException and e.response:
        content = e.content
    if len(path) > 2 and path[2] in ['item']:
        return render_template_string(GathermateException.VIEW_ERROR_TEMPLATE,
                                      msg=err_message,
                                      response=content)
    return render_template('scrapmate/index.html',
                           error_msg=err_message,
                           response=content)


class Pagination(object):

    def __init__(self, page, max_page):
        self.page = page
        self.max_page = max_page

    @property
    def pages(self):
        return self.max_page

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=1, left_current=2,
                   right_current=3, right_edge=1):
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
