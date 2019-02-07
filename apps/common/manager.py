# -*- coding: utf-8 -*-

import os
import glob
import inspect
import importlib
import logging as log

from apps.common.exceptions import MyFlaskException


class Manager(object):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        if not config:
            raise MyFlaskException('Config is not set.')
        self.__config = config

    @property
    def config(self):
        # type: () -> flask.config.Config
        return self.__config

    @config.setter
    def config(self, value):
        raise MyFlaskException('Not allowed.')

    def _register_modules(self, package, module_type, parent_class=None):
        # type: (str, str, Optional[type]) -> Dict[str, Union[type, module]]
        modules = {}
        modules_path = '{}/'.format(os.path.join(self.__config['ROOT_DIR'], package.replace('.', '/')))
        for file in glob.iglob("{}[!_]*.py".format(modules_path)):
            fname, fext = os.path.splitext(os.path.basename(file))
            module = importlib.import_module('{}.{}'.format(package, fname))
            try:
                type_, class_ = module.register()
            except AttributeError:
                MyFlaskException.trace_error()
                log.warning('[%s%s] has not register() function.', fname, fext)
                continue
            if type_ == module_type:
                modules.update({class_.__name__: class_})
                log.debug("%s class is registered as %s.", class_.__name__, type_)
        return modules

    def _get_class_of(self, module, class_):
        # type: (module, type) -> Generator[Tuple[str, type]]
        for tuple_ in inspect.getmembers(module, inspect.isclass):
            for base in tuple_[1].__bases__:
                if base is class_:
                    yield tuple_[1].__name__, tuple_[1]
