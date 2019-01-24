# -*- coding: utf-8 -*-
import os
import inspect
import importlib
import glob
import logging as log

import packer
import gatherer as gtr
from apps.common import fetchers
from apps.common.exceptions import MyFlaskException
from apps.common import toolbox as tb
from apps.common import urldealer as ud

def hire_manager(config):
    # type: (flask.config.Config, Text) -> gathermate.Manager
    manager = FlaskManager(config)
    packer.ACCEPTED_EXT = config.get('ACCEPTED_EXT', [])
    return manager


class Manager(object):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        if not config:
            raise MyFlaskException('Config is not set.')
        self.__config = config
        self.__gatherer_classes = self._register_modules('gatherers')

    def _register_modules(self, package):
        # type: (Text) -> Dict[Text, Type[gatherer.Gatherer]]
        modules = {}
        root = os.path.dirname(os.path.abspath(__file__))
        modules_path = '{}/'.format(os.path.join(root, package))
        for file in glob.iglob("{}[!_]*.py".format(modules_path)):
            fname, fext = os.path.splitext(os.path.basename(file))
            module = importlib.import_module('apps.gathermate.{}.{}'.format(package, fname))
            try:
                type_ = module.register()
            except AttributeError:
                MyFlaskException.trace_error()
                log.warning('[%s%s] has not register() function.', fname, fext)
                continue
            if type_ == 'Gatherer':
                for name, class_ in self._get_class_of(module, gtr.Gatherer):
                    modules[ud.URL(class_.URL).hostname] = class_
                    log.debug("%s class is registered as %s.", name, type_)
            elif type_ == 'Plugin':
                # Plugin was not implemented yet.
                modules[fname] = module
                log.debug('%s is registered as plugin.', fname)

        return modules

    def _get_class_of(self, module, class_):
        # type: (module, class) -> Generator[Tuple[Text, Type[Any]]]
        for tuple_ in inspect.getmembers(module, inspect.isclass):
            for base in tuple_[1].__bases__:
                if base is class_:
                    yield tuple_[1].__name__, tuple_[1]

    def _hire_gatherer(self, target):
        # type: (urldealer.URL) -> Type[gatherer.Gatherer]
        host = target.hostname if target.hostname else target.netloc
        if not host:
            raise MyFlaskException('Target URL is wrong : %s' % target.text)
        try:
            class_ = self.__gatherer_classes[host]
        except KeyError:
            MyFlaskException.trace_error()
            class_ = self._find_gatherer(host)
        log.debug("%s class matches with [%s].", class_.__name__, target.text)
        return self._train_gatherer(class_, self.__config.get('GATHERERS'))

    def _find_gatherer(self, alias):
        # type: (Text) -> Type[gatherer.Gatherer]
        for host, class_ in self.__gatherer_classes.items():
            if alias in host:
                log.debug("%s class matches with [%s].", class_.__name__, alias)
                return class_
        raise MyFlaskException('There is no class associate with : {}'.format(alias))

    def _train_gatherer(self, class_, config):
        # type: (Type[gatherer.Gatherer], Dict[Text, object]) -> Type[gatherer.Gatherer]
        instance_config = self._get_default_config(class_.__name__, config)
        gatherer = class_(instance_config, fetchers.hire_fetcher(self.__config))
        log.debug("%s instance has been created.", type(gatherer).__name__)
        return gatherer

    def _get_default_config(self, name, config):
        # type: (Text, Dict[Text, object]) -> Dict[Text, object]
        default_config = {
            'ENCODING': 'utf-8',
            'RSS_WANT': self.__config.get('RSS_WANT', []),
            'RSS_AGGRESSIVE': self.__config.get('RSS_AGGRESSIVE', False),
            'RSS_ASYNC': self.__config.get('RSS_ASYNC', False),
            'RSS_WORKERS': self.__config.get('RSS_WORKERS', 1),
            'RSS_LENGTH': self.__config.get('RSS_LENGTH', 5),
        }
        if config and config.get(name, None):
            for k, v in config.get(name).items():
                default_config[k] = v
        return default_config

    def _order_rss(self, target, query_dict):
        # type: (urldealer.URL, Dict[Text, Union[Text, int]]) -> str
        gatherer = self._hire_gatherer(target)
        gatherer.isRSS = True
        length = int(query_dict.get('length', 0))
        if not length == 0:
            gatherer.length = length
        listing = gatherer.parse_list(target)
        return packer.pack_rss(gatherer.parse_items(listing))

    def _order_item(self, target, query_dict):
        # type: (urldealer.URL, Dict[Text, Union[Text, int]]) -> List[object]
        gatherer = self._hire_gatherer(target)
        items = gatherer.parse_item(target)
        return packer.pack_item(items)

    def _order_list(self, target, query_dict):
        # type: (urldealer.URL, Dict[Text, Union[Text, int]]) -> Dict[Text, object]
        gatherer = self._hire_gatherer(target)
        listing = gatherer.parse_list(target)
        return packer.pack_list(listing)

    def _order_down(self, target, query_dict):
        # type: (urldealer.URL, Dict[Text, Union[Text, int]]) -> Response
        ticket = query_dict.get('ticket', None)
        if ticket:
            ticket = ud.split_qs(ud.unquote(query_dict.get('ticket')))
            gatherer = self._hire_gatherer(ud.URL(ticket['referer']))
            return gatherer.parse_file(target, ticket)
        # RSS_AGGRESSIVE = False
        gatherer = self._hire_gatherer(target)
        gatherer.isRSS = True
        item = gatherer.parse_item(target)
        if item['type'] in ['magnet', 'link']:
            return item['link']
        return gatherer.parse_file(ud.URL(item['link']), item['ticket'])

    def _order_page(self, target, query_dict):
        # type: (urldealer.URL, Dict[Text, Union[Text, int]]) -> Iterable
        gatherer = self._hire_gatherer(target)
        return gatherer.get_page(gatherer.fetch(target))

    @tb.timeit
    def _get_data(self, order, target, query_dict):
        # type: (Text, urldealer.URL, Union[Dict, ImmutableMultiDict]) -> Optional[Text, Response, Iterable]
        search_key = query_dict.get('search', None)
        if search_key:
            target.update_qs('search={}'.format(search_key))
        page_num = int(query_dict.get('page', 0))
        if page_num > 0:
            target.update_qs('page={}'.format(page_num))
        log.info('%s mode', order.upper())
        data = getattr(self, '_order_{}'.format(order))(target, query_dict)
        log.info('Cumulative fetching size : %s', fetchers.fetcher.size_text(fetchers.fetcher.cum_size))
        return data

    def request(self):
        raise NotImplementedError

    def request_by_alias(self):
        raise NotImplementedError


class FlaskManager(Manager):

    def request(self, order, request_url):
        # type: (Text, Text) -> Optional[Text, Response, Iterable]
        request = ud.URL(request_url)
        try:
            url = request.query_dict['url']
            if url:
                target = ud.URL(ud.unquote(url))
            else:
                raise MyFlaskException('There is no target page')
        except KeyError:
            raise KeyError('There is no target page : {}'.format(request.query))

        return self._get_data(order, target, request.query_dict)

    def request_by_alias(self, order, site, board, query):
        # type: (Text, Text, Text, ImmutableMultiDict) -> Optional[Text, Response, Iterable]
        class_ = self._find_gatherer(site)
        if order in ['list', 'rss']:
            target = ud.URL(class_.LIST_URL % board)
        else:
            target = None
        return self._get_data(order, target, query)
