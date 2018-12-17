# -*- coding: utf-8 -*-
import os
import traceback
import logging
import sys
import importlib

from flask import Flask
from flask import request
from flask import send_from_directory
from flask import render_template
from flask import render_template_string
from flask import flash
from flask import redirect

from util.cache import cache
from util.auth import auth
from util import logger
from util import toolbox
from util import urldealer as ud

reload(sys)
sys.setdefaultencoding('utf-8')

def create_app(config_instance, cache_type, backend):
    # type: () -> flask.app.Flask

    # Make flask instance
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')

    # config.py (default) : It has instances of Localhost and GoogleAppEngine.
    app.config.from_object('config')
    # instance/config.py (user) : It also has instances of Localhost and GoogleAppEngine.
    app.config.from_pyfile('config.py', silent=True)
    # Overwrite app config from a instance created by config.py or instance/config.py if it exists.
    app.config.from_object(app.config[config_instance])
    logging.debug('Config: %s', app.config['NAME'])
    app.config['BACKEND'] = backend

    logger.config(backend, app.config['LOG_LEVEL'])

    cache.init_app(app, config=cache_type)
    with app.app_context():
        cache.clear()
    auth.init_app(app)

    # Register blueprints from config.
    for blue, setting in app.config['BLUEPRINTS'].items():
        try:
            blueprint = getattr(importlib.import_module(
                setting['package']),
                setting['instance'])
            app.register_blueprint(
                blueprint,
                url_prefix=setting['url_prefix'])
            logging.debug(
                '{} has been registered as Blueprint.'.format(blueprint.name))
        except:
            logging.error('\n{}'.format(traceback.format_exc()))

    # Register a manager from config.
    manager = importlib.import_module(app.config['MANAGER'])
    app.mgr = manager.hire_manager(app.config)

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
@auth.requires_auth
def unhandled_exception(e):
    # type: (Type[Exception]) -> Text
    logging.error('\n{}'.format(traceback.format_exc()))
    flash(e.message)
    target = request.args.get('url')
    content = ''
    path = request.path.split('/')

    if target:
        url = ud.URL(ud.unquote(target))
        key = app.mgr.fetcher._create_key(url, request.form)
        r = cache.get(key)
        if r:
            content = toolbox.decode(r.content)
            logging.debug('Loaded response content for handling exception.')

    if len(path) > 2 and path[2] in ['item']:
        return render_template_string(error_template,
                                      msg=e.message,
                                      response=content)
    return render_template('gathermate_index.html',
                           error_msg=e.message,
                           response=content)

error_template = '''
<i class="fa fa-exclamation-triangle" aria-hidden="true"></i> {{ msg }}
{% if response %}
<script>
  $(".view_response").off("click");
  $(".view_response").on("click", function(e){
    toggle($(this).children().first());
  });
</script>
<div class="view_response" style="cursor:pointer;">
  >>Toggle Response<<
  <div style="display:none;">
    <pre>{{ response }}</pre>
  </div>
</div>
{% endif %}
{% with messages = get_flashed_messages() %}
    {% if messages %}
        {% for message in messages %}
            <script>
                toastbar('{{ message }}');
            </script>
        {% endfor %}
    {% endif %}
{% endwith %}
'''
