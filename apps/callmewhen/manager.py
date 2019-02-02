# -*- coding: utf-8 -*-

import logging as log
import json

from apps.common.manager import Manager
from apps.common.exceptions import MyFlaskException
from apps.common import fetchers
from apps.common import urldealer as ud
from apps.common.cache import cache

def hire_manager(config):
    # type: (flask.config.Config, Text) -> Manager
    return CallMeWhenManager(config)


class CallMeWhenManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(CallMeWhenManager, self).__init__(config)

    def request(self, order, query):
        # type: (str, werkzeug.datastructures.MultiDict) -> None
        if order == 'send':
            messenser = Telegram(self.config)
            return messenser.send(query.get('sender', None), query.get('msg', ''))
        return 'Done.'

class Messenser(object):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        self.config = config

    def fetch(self, *args, **kwargs):
        fetcher = fetchers.hire_fetcher(self.config)
        return fetcher.fetch(*args, **kwargs)

    def send(self):
        raise NotImplementedError

class Telegram(Messenser):
    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(Telegram, self).__init__(config)
        self.__token = self.config['TELEGRAM_BOT_TOKEN']
        self.base_url = 'https://api.telegram.org/bot%s/' % self.token
        self.chat_ids = []
        self.key = cache.create_key('telegram-chat-ids')

    @property
    def token(self):
        return self.__token

    @token.setter
    def token(self, value):
        raise MyFlaskException('Not allowed.')

    def send(self, sender, text, parse_mode=None, disable_web_page_preview=False,
                    disable_notification=False, reply_to_message_id=None, reply_markup=None):
        if not self.getUpdates():
            return 'Telegram bot token wasn\'t set.'
        url = ud.URL(self.base_url + 'sendMessage')
        message = {
            'chat_id': self.chat_ids[0],
            'text': '{}: {}'.format(sender, text) if sender else text,
            'parse_mode': parse_mode or '',
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification,
            'reply_to_message_id': reply_to_message_id or '',
            'reply_markup': reply_markup or '',
        }
        response = self.fetch(url, payload=message, method='JSON', forced_update=True)
        return self.handle_response(response)

    def getUpdates(self):
        if self.token is None:
            log.warning('Telegram bot token wasn\'t set.')
            return False
        url = ud.URL(self.base_url + 'getUpdates')
        return self.handle_response(self.fetch(url))

    def handle_response(self, response):
        js = json.loads(response.content)
        if js.get('ok', False):
            cached = cache.get(self.key)
            if not cached:
                self.chat_ids = list(self.get_chat_ids(js.get('result')))
                cache.set(self.key, ','.join([str(id_) for id_ in self.chat_ids]), timeout=0)
            else:
                self.chat_ids = map(int, cached.split(','))
        else:
            raise MyFlaskException('Telegram responded : %s' % js)
        return (response.content, response.status_code, response.headers)

    def get_chat_ids(self, result):
        if result:
            return set([item['message']['chat']['id'] for item in result])
        else:
            raise MyFlaskException('There is no message to update. You should send a new message to bot.')
