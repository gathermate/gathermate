# -*- coding: utf-8 -*-

import logging
from logging.config import dictConfig

def config(software, level):
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
            'level': level,
            'handlers': ['default']
        }
    })
    root = logging.getLogger()
    # chardet decode() logs TMI on DEBUG level.
    chardet_logger = logging.getLogger('chardet.charsetprober')
    chardet_logger.setLevel('INFO')
    if software.startswith('gunicorn/'):
        '''
        Gunicorn handler is about how logs are outputted.
        Root logger is about how logs are inputted.
        So if you wrote logs to root logger,
        you should register gunicorn handlers(output) on root logger(input).
        Logger class : gunicorn.glogging.Logger
        '''
        gunicorn_logger = logging.getLogger('gunicorn.error')
        root.handlers = gunicorn_logger.handlers
        root.setLevel(gunicorn_logger.level)
        return
