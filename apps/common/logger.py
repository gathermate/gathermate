# -*- coding: utf-8 -*-

import logging
from logging.config import dictConfig

def config(software, level):
    root = logging.getLogger()
    root.setLevel(level)
    if software == 'GoogleAppEngine':
        return
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '%(asctime)s '
                      '%(levelname)8s: '
                      '%(message)s '
                      '<%(name)s:%(filename)s:%(lineno)d>',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }},
        'handlers': {
            'default': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'default'
            },
        },
        'root': {
            'handlers': ['default']
        }
    })
    # chardet decode() logs TMI on DEBUG level.
    chardet_logger = logging.getLogger('chardet.charsetprober')
    chardet_logger.setLevel('WARNING')
    urllib3_logger = logging.getLogger('urllib3.connectionpool')
    urllib3_logger.setLevel('WARNING')
    werkzeug = logging.getLogger('werkzeug')
    werkzeug.setLevel('WARNING')
    if software.startswith('gunicorn/'):
        '''
        The logger of logging is about how logs are inputted.
        The handler of logging is about how logs are outputted.
        So if you want to write logs by root logger, and print them by gunicorn,
        you should register gunicorn handlers(output) on root logger(input).
        Logger class : gunicorn.glogging.Logger
        '''
        gunicorn_logger = logging.getLogger('gunicorn.error')
        root.handlers = gunicorn_logger.handlers
        root.setLevel(gunicorn_logger.level)
