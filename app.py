# -*- coding: utf-8 -*-

import os
import sys
import importlib
import threading

from flask import Flask
from flask import request
from flask import send_from_directory
from flask import render_template

from apps.common import logger
from apps.common import caching
from apps.common.exceptions import GathermateException
from apps.common import urldealer as ud
from apps.common.datastructures import MultiDict
from apps.common import fetchers

reload(sys)
sys.setdefaultencoding('utf-8')

def create_app():
    root_dir = os.path.dirname(os.path.realpath(__file__))
    configs = [
        os.environ.get('GATHERMATE_CONFIG', ''),
        os.path.join(root_dir, 'instance/config.py'),
        os.path.join(root_dir, 'install/user_config.py'),
    ]
    config_path = [config for config in configs if os.path.exists(config)]
    if len(config_path) is 0:
        os.system('echo "No config file found."')
        sys.exit(1)
    else:
        config_path = config_path[0]
    # Make flask instance
    instance_path = os.path.dirname(config_path)
    static_folder = instance_path + '/static' if os.path.exists(instance_path + '/static') else 'static'
    template_folder = instance_path + '/templates' if os.path.exists(instance_path + '/templates') else 'templates'
    app = Flask(__name__,
                instance_path=instance_path,
                instance_relative_config=True,
                static_folder=static_folder,
                template_folder=template_folder)
    # Set configuration.
    app.config.from_pyfile(os.path.basename(config_path), silent=True)
    app.config['SERVER_SOFTWARE'] = os.environ.get('SERVER_SOFTWARE', '')
    software = app.config.get('SERVER_SOFTWARE')
    if software.startswith('Google App Engine/') or software.startswith('Development/'):
        software = 'GoogleAppEngine'
        config_instance = 'GOOGLEAPPENGINE'
        cache_type = {'CACHE_TYPE': 'memcached'}
    else:
        config_instance = 'LOCALHOST'
        cache_type = {'CACHE_TYPE': 'simple'}
    app.config.from_object(app.config.get(config_instance + '_INSTANCE'))
    logger.config(software, app.config['LOG_LEVEL'])
    app.logger.setLevel(app.config['LOG_LEVEL'])
    app.logger.info('Server Software: %s', software)
    app.logger.info('Config: %s in %s', app.config['NAME'], config_path)
    caching.init(app, app.config, cache_type)
    # Register apps from config.
    app.managers = {}
    should_send = False
    for app_config in app.config.get('APPS'):
        app_config.update(ROOT_DIR=app.root_path,
                          FETCHER=app.config['FETCHER'],
                          CONFIG_DIR=app.instance_path)
        if app_config['NAME'] == 'Streamate':
            app_config['CHANNELS'] = app.config['CHANNELS']
        app.managers[app_config['NAME']] = importlib.import_module(app_config['MANAGER']).hire_manager(app_config)
        if app_config.get('BLUEPRINT') is not None:
            bp = getattr(importlib.import_module(
                app_config['BLUEPRINT']),
                app_config['BLUEPRINT_INSTANCE'])
            app.register_blueprint(
                bp,
                url_prefix=app_config['BLUEPRINT_URL_PREFIX'])
            app.logger.info('{} has been registered as Blueprint.'.format(bp.name))
        if app_config['NAME'] == 'Callmewhen':
            should_send = app_config['NOTIFY']
    # Register a function for sending messages to telegram bot.
    def send(sender, msg):
        if should_send:
            threading.Thread(target=app.managers['Callmewhen'].request, args=('send', {'msg':msg, 'sender': sender})).start()
    app.send = send
    return app

app = create_app()

# Run as main.
if __name__ == '__main__':
    app.run()

@app.route('/robots.txt')
def to_robots():
    return send_from_directory(app.static_folder, request.path[1:])

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    return render_template('default.html')

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if url:
        fetcher = fetchers.hire_fetcher(**{k.lower(): v for k, v in app.config.get('FETCHER').iteritems()})
        r = fetcher.fetch(url, follow_redirects=True)
        return r.content, r.status_code
    return render_template('proxy.html')

@app.route('/404')
def not_found_test():
    return page_not_found(Exception())

@app.route('/500')
def server_error_test():
    return internal_server_error(Exception())

@app.before_request
def before_request_to_do():
    request.args = MultiDict(request.args.iteritems(multi=True))
    app.logger.debug('%(line)s Start %(request)s', {'line': '-'*30, 'request': request})
    client = '{} requested {} from {}'.format(request.remote_addr, request.full_path, request.referrer)
    app.logger.debug(client)

@app.after_request
def after_request_to_do(response):
    return response

@app.teardown_request
def teardown_requst_to_do(exception):
    if exception is not None:
        app.logger.error("Teardown request : {0!r}".format(exception))
    app.logger.debug('%(line)s End %(request)s', {'line': '-'*30, 'request': request})

@app.errorhandler(Exception)
def unhandled_exception(e):
    GathermateException.trace_error()
    if hasattr(e, 'message') and e.message != '':
        err_message = e.message
    else:
        err_message = str(e)
    app.send('{}#{}'.format(__name__, request.host), err_message)
    if hasattr(e, 'response') and e.response is not None:
        return e.response.content, e.response.status_code, dict(e.response.headers)
    return err_message, 404

@app.errorhandler(404)
def page_not_found(e):
    return '404 Not Found...', 404

@app.errorhandler(500)
def internal_server_error(e):
    return '500 Internal Server Error...', 500

@app.template_filter('quote')
def quote_filter(url):
    return ud.quote(url)
