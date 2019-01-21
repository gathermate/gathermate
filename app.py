# -*- coding: utf-8 -*-
import os
import logging
import sys
import importlib

from flask import Flask
from flask import request
from flask import send_from_directory
from flask import render_template

from apps.common.auth import auth
from apps.common.cache import cache
from apps.common.exceptions import MyFlaskException
from apps.common import logger
from apps.common import urldealer as ud

reload(sys)
sys.setdefaultencoding('utf-8')

def create_app(config_instance, cache_type, backend):
    # type: () -> flask.app.Flask
    # Make flask instance
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')
    # instance/config.py : It has instances of Localhost and GoogleAppEngine.
    app.config.from_pyfile('config.py', silent=True)
    # Overwrite app config from a instance(Localhost or GoogleAppEngine) created by instance/config.py
    app.config.from_object(app.config[config_instance])
    logging.debug('Config: %s', app.config['NAME'])
    app.config['BACKEND'] = backend
    logger.config(backend, app.config['LOG_LEVEL'])
    cache.init_app(app, config=cache_type)
    with app.app_context():
        cache.clear()
        cache.APP_SECRET_KEY = app.config.get('SECRET_KEY', '')
        cache.APP_TIMEOUT = app.config.get('TIMEOUT', 10)
        cache.FETCHER_TIMEOUT = app.config['FETCHER'].get('CACHE_TIMEOUT', 120)
        cache.FETCHER_COOKIE_TIMEOUT = app.config['FETCHER'].get('COOKIE_TIMEOUT', 3600)
        cache.create_key = lambda url_text, payload=None : \
            '{}-{}'.format(cache.APP_SECRET_KEY,
                           '{}?{}'.format(url_text,
                                          ud.unsplit_qs(payload)) if payload else url_text)
    auth.init_app(app)
    # Register blueprints from config.
    for name, settings in app.config['BLUEPRINTS'].items():
        try:
            blueprint = getattr(importlib.import_module(
                settings['module']),
                settings['instance'])
            app.register_blueprint(
                blueprint,
                url_prefix=settings['url_prefix'])
            logging.debug(
                '{} has been registered as Blueprint.'.format(blueprint.name))
        except:
            MyFlaskException.trace_error()
    # Register managers from config.
    app.managers = {}
    for name, module in app.config['MANAGERS'].items():
        app.managers[name] = importlib.import_module(module).hire_manager(app.config)
    return app

# Before create flask...
backend = os.environ.get('SERVER_SOFTWARE', '')
if backend.startswith('Google App Engine/') or backend.startswith('Development/'):
    backend = 'GoogleAppEngine'
    config_instance = 'GOOGLEAPPENGINE'
    cache_type = {'CACHE_TYPE': 'memcached'}
else:
    config_instance = 'LOCALHOST'
    cache_type = {'CACHE_TYPE': 'simple'}
app = create_app(config_instance, cache_type, backend)
if __name__ == '__main__':
    app.run()

@app.route('/robots.txt')
def to_robots():
    # type: () -> flask.wrappers.Response
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    # type: (str) -> Text
    return render_template('default.html')

@app.before_request
def before_request_to_do():
    # type: () -> None
    logging.debug('%(line)s Start of the request', {'line': '-'*30})
    logging.info(
        '[%s] requested [%s] from [%s]',
        request.remote_addr, request.full_path, request.referrer)

@app.after_request
def after_request_to_do(response):
    # type: (flask.wrappers.Response) -> flask.wrappers.Response
    return response

@app.teardown_request
def teardown_requst_to_do(exception):
    # type: () -> None
    if exception:
        logging.error(exception.message)
    logging.debug('%(line)s End of the request', {'line': '-'*30})

@app.errorhandler(Exception)
def unhandled_exception(e):
    return e.message
