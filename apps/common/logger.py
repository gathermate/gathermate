# -*- coding: utf-8 -*-

import logging

def config(backend, level):
    root = logging.getLogger()
    # chardet decode() logs TMI on DEBUG level.
    chardet_logger = logging.getLogger('chardet.charsetprober')
    chardet_logger.setLevel('INFO')
    if backend == 'GoogleAppEngine':
        return
    if backend.startswith('gunicorn/'):
        '''
        Gunicorn handler is about how logs are outputted.
        Root logger is about how logs are inputted.
        So if you wrote logs to root logger,
        you should register gunicorn handlers(output) on root logger(input).
        '''
        gunicorn_logger = logging.getLogger('gunicorn.error')
        root.handlers = gunicorn_logger.handlers
        root.setLevel(gunicorn_logger.level)
        chardet_logger.handlers = gunicorn_logger.handlers
        return
    formatter = logging.Formatter(
        '%(asctime)s '
        '%(levelname)8s: '
        '%(message)s '
        '<%(filename)s:%(lineno)d>',
        '%Y-%m-%d %H:%M:%S'
    )
    for handler in root.handlers:
        handler.setFormatter(formatter)
    root.setLevel(level)
