# -*- coding: utf-8 -*-

import logging

from flask import Blueprint
from flask import request
from flask import current_app as app

from apps.common.auth import auth

log = logging.getLogger(__name__)
name = 'Callmewhen'
cmw = Blueprint(
    name,
    __name__,
    template_folder='templates',
    static_folder='static')

@cmw.route('/<string:order>', methods=['GET'])
@auth.requires_auth
def send(order):
    # type: () -> Text
    return app.managers[name].request(order, request.args)