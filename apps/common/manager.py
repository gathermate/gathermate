# -*- coding: utf-8 -*-

import os
import glob
import imp
import inspect
import importlib
import logging

from apps.common.exceptions import GathermateException
from apps.common import fetchers

log = logging.getLogger()

class Manager(object):

    def __init__(self, config):
        if not config:
            raise GathermateException('Config is not set.')
        self.__config = config

    @property
    def config(self):
        return self.__config

    @config.setter
    def config(self, value):
        raise GathermateException('Not allowed.')

    def _register_modules(self, package, module_type, parent_class=None):
        modules = {}
        default_path = os.path.join(self.config['ROOT_DIR'], package.replace('.', '/'))
        user_path = os.path.join(self.config['CONFIG_DIR'], default_path.split('/')[-1])
        for m_path in [default_path, user_path]:
            for file in glob.iglob("{}/[!_]*.py".format(m_path)):
                fname, fext = os.path.splitext(os.path.basename(file))
                if m_path == default_path:
                    module = importlib.import_module('{}.{}'.format(package, fname))
                elif m_path == user_path:
                    module = imp.load_source(package, file)
                try:
                    type_, class_ = module.register()
                except AttributeError:
                    log.warning('[%s%s] doesn\'t have register() function.', fname, fext)
                    continue
                if type_ == module_type:
                    if class_.__name__ in modules:
                        log.info("%s class is overridden from %s", class_.__name__, file)
                    else:
                        log.info("%s class is registered as %s", class_.__name__, type_)
                    modules.update({class_.__name__: class_})
        return modules

    def _get_class_of(self, module, class_):
        for tuple_ in inspect.getmembers(module, inspect.isclass):
            for base in tuple_[1].__bases__:
                if base is class_:
                    yield tuple_[1].__name__, tuple_[1]

    def _hire_fetcher(self):
        fetcher_config = {k.lower(): v for k, v in self.config['FETCHER'].iteritems() if k != 'COOKIE_TO_FILE'}
        cookie_path=os.path.join(self.config['CONFIG_DIR'], 'cookies') if self.config['FETCHER']['COOKIE_TO_FILE'] else None
        return fetchers.hire_fetcher(cookie_path=cookie_path, **fetcher_config)
