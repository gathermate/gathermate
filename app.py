# -*- coding: utf-8 -*-
import os
import sys
import importlib

import click
from flask import Flask
from flask import request
from flask import send_from_directory
from flask import render_template
from flask import url_for

from apps.common import caching
from apps.common.exceptions import MyFlaskException
from apps.common import logger
from apps.common import urldealer as ud

reload(sys)
sys.setdefaultencoding('utf-8')

def create_app(software, config, cache_type):
    # type: () -> flask.app.Flask
    # Make flask instance
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')
    # Set configuration.
    app.config.from_object('default_config.' + config)
    app.config.from_pyfile('config.py', silent=True)
    app.config['SOFTWARE'] = software
    app.config['ROOT_DIR'] = os.path.dirname(os.path.abspath(__file__))
    app.config['URL_FOR'] = url_for
    logger.config(software, app.config['LOG_LEVEL'])
    app.logger.info('Server Software: %s', software)
    app.logger.info('Config: %s', app.config['NAME'])
    caching.init(app, app.config, cache_type)
    # Register blueprints from config.
    for name, settings in app.config['BLUEPRINTS'].items():
        if software == 'GoogleAppEngine' and name == 'Streamate':
            continue
        try:
            blueprint = getattr(importlib.import_module(
                settings['module']),
                settings['instance'])
            app.register_blueprint(
                blueprint,
                url_prefix=settings['url_prefix'])
            app.logger.info(
                '{} has been registered as Blueprint.'.format(blueprint.name))
        except:
            MyFlaskException.trace_error()
    # Register managers from config.
    app.managers = {}
    for name, module in app.config['MANAGERS'].items():
        if software == 'GoogleAppEngine' and name == 'Streamate':
            continue
        app.managers[name] = importlib.import_module(module).hire_manager(app.config)
    # Register a function for sending messages to telegram bot.
    def send(sender, msg):
        if app.config.get('NOTIFY', False) and app.managers.get('Callmewhen', None):
            result = app.managers['Callmewhen'].request('send',
                                                        {'msg':msg, 'sender': sender})
            if result:
                app.logger.debug('The message was sent.')
            else:
                app.logger.warning('The message wasn\'t sent.')
    app.send = send
    return app

# Before create flask...
software = os.environ.get('SERVER_SOFTWARE', '')
if software.startswith('Google App Engine/') or software.startswith('Development/'):
    software = 'GoogleAppEngine'
    config = software
    cache_type = {'CACHE_TYPE': 'memcached'}
else:
    config = 'Localhost'
    cache_type = {'CACHE_TYPE': 'simple'}
app = create_app(software, config, cache_type)

# Run as main.
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
    app.logger.debug('%(line)s Start %(request)s', {'line': '-'*30, 'request': request})
    client = '{} requested {} from {}'.format(request.remote_addr, request.full_path, request.referrer)
    app.logger.debug(client)


@app.after_request
def after_request_to_do(response):
    # type: (flask.wrappers.Response) -> flask.wrappers.Response
    return response

@app.teardown_request
def teardown_requst_to_do(exception):
    # type: () -> None
    if exception is not None:
        app.logger.error("Teardown request {0!r}".format(exception))
    app.logger.debug('%(line)s End %(request)s', {'line': '-'*30, 'request': request})

@app.errorhandler(Exception)
def unhandled_exception(e):
    # type: (Type[Exception]) -> Text
    MyFlaskException.trace_error()
    app.send('{}#{}'.format(__name__, request.host), e.message)
    if e.response is not None:
        return e.response.content, e.response.status_code, dict(e.response.headers)
    else:
        return e.message, 404

@app.template_filter('quote')
def quote_filter(url):
    return ud.quote(url)

@app.cli.command('send')
@click.argument('sender', nargs=1)
@click.argument('message', nargs=1)
def send_message(sender, message):
    app.send(sender + '#CLI', message)
