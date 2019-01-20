# -*- coding: utf-8 -*-
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

from apps.common.cache import cache
from apps.common.auth import auth
from apps.common.exceptions import MyFlaskException

gathermate = Blueprint(
    'Gathermate',
    __name__,
    template_folder='templates',
    static_folder='static')

def make_cache_key():
    # type: () -> Text
    return cache.create_key(request.url, payload=request.form)

@gathermate.route('/', strict_slashes=False)
@auth.requires_auth
def index():
    # type: () -> Text
    return render_template('gathermate_index.html')

@gathermate.route('/encode', methods=['GET'])
@auth.requires_auth
def quote():
    # type: () -> Text
    return render_template('gathermate_encode.html')

@gathermate.route('/<string:site>/<string:board>/rss', methods=['GET'])
@cache.cached(key_prefix=make_cache_key, timeout=cache.APP_TIMEOUT)
@auth.requires_auth
def rss_by_alias(site, board):
    # type: (Text, Text) -> Text
    data = app.manager.request_by_alias('rss', site, board, request.args)
    return order_rss(data)

@gathermate.route('/<string:site>/<string:board>', methods=['GET'])
@cache.cached(key_prefix=make_cache_key, timeout=cache.APP_TIMEOUT)
@auth.requires_auth
def list_by_alias(site, board):
    # type: (Text, Text) -> Text
    data = app.manager.request_by_alias('list', site, board, request.args)
    return order_list(data)

@gathermate.route('/<string:order>', methods=['GET'])
@cache.cached(key_prefix=make_cache_key, timeout=cache.APP_TIMEOUT)
@auth.requires_auth
def order(order):
    # type: (Text) -> Union[unicode, flask.wrappers.Response]
    ''' Do not name order()'s args with query names ex) path, netloc, scheme etc... '''
    data = app.manager.request(order, request.url)
    return globals()['order_{}'.format(order)](data)

def order_rss(data):
    # type: (Text) -> flask.wrappers.Response
    return Response(data, mimetype='text/xml')

def order_down(data):
    # type: (Union[Text, Response]) -> flask.wrappers.Response
    try:
        return send_file(BytesIO(data.content),
                         as_attachment=True,
                         mimetype=data.headers['content-type'],
                         attachment_filename=data.filename)
        #return data.content, data.status_code, data.headers.items()
    except AttributeError:
        return redirect(data)

def order_list(data):
    # type: (Dict[Text, object]) -> Text
    pagination = Pagination(data['current_page'], data['max_page'])
    return render_template('gathermate_list.html',
                           index=request.args.get('index'),
                           pagination=pagination,
                           title='Gathermate',
                           search=request.args.get('search'),
                           articles=data['articles'])

def order_item(data):
    # type: (List[Dict[Text, object]]) -> Text
    return render_template('gathermate_view.html', items=data)

def order_page(data):
    # type: (Iterable) -> Text
    return data

@gathermate.errorhandler(Exception)
@auth.requires_auth
def unhandled_exception(e):
    # type: (Type[Exception]) -> Text
    MyFlaskException.trace_error()
    flash(e.message)
    path = request.path.split('/')
    content = None
    if type(e) is MyFlaskException and e.response:
        content = e.content
    if len(path) > 2 and path[2] in ['item']:
        return render_template_string(MyFlaskException.VIEW_ERROR_TEMPLATE,
                                      msg=e.message,
                                      response=content)
    return render_template('gathermate_index.html',
                           error_msg=e.message,
                           response=content)


class Pagination(object):

    def __init__(self, page, max_page):
        # type: (int, int) -> None
        self.page = page
        self.max_page = max_page

    @property
    def pages(self):
        # type: () -> int
        return self.max_page

    @property
    def has_prev(self):
        # type: () -> bool
        return self.page > 1

    @property
    def has_next(self):
        # type: () -> bool
        return self.page < self.pages

    def iter_pages(self, left_edge=1, left_current=2,
                   right_current=3, right_edge=1):
        # type: (Optional[int, int, int, int]) -> Union[int, None]
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