# -*- coding: utf-8 -*-
import logging as log
from functools import wraps

from flask import request
from flask import Response


class Auth(object):

    def init_app(self, app):
        # type: (flask.app.Flask) - None
        self.app = app

    def requires_auth(self, f):
        # type: (Callable) -> Callable
        def check_auth(username, password):
            return username == self.app.config['AUTH_ID'] \
                        and password == self.app.config['AUTH_PW']

        def authenticate():
            log.info('[%s] was denied with [%s]',
                     request.remote_addr, request.full_path)
            return Response('Could not verify your access level.',
                            401,
                            {'WWW-Authenticate': 'Basic realm="Login Required"'})

        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            log.info('[%s] was accepted with [%s]',
                     request.remote_addr, request.path)
            return f(*args, **kwargs)
        return decorated

auth = Auth()
