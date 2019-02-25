# -*- coding: utf-8 -*-

import logging
from functools import wraps

from flask import request
from flask import Response

from apps.common import caching

log = logging.getLogger(__name__)

class Auth(object):

    def requires_auth(self, f):
        # type: (Callable) -> Callable
        def check_auth(username, password):
            return username == caching.config['AUTH_ID'] \
                        and password == caching.config['AUTH_PW']

        def authenticate():
            denied = '[{}] was denied with [{}]'.format(request.remote_addr, request.full_path)
            log.debug(denied)
            return Response('Could not verify your access level.',
                            401,
                            {'WWW-Authenticate': 'Basic realm="Login Required"'})

        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not check_auth(auth.username, auth.password):
                return authenticate()
            log.debug('[%s] was accepted with [%s]',
                     request.remote_addr, request.path)
            return f(*args, **kwargs)
        return decorated

auth = Auth()
