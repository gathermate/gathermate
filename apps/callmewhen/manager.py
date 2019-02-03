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
        # type: (str, Type[Dict[str, Union[List[str], str]]]) -> ?
        if order == 'send':
            messenser = Telegram(self.config)
            return messenser.send(query.get('sender', None), query.get('msg', ''))

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
        self.__TOKEN = self.config['TELEGRAM_BOT_TOKEN']
        self.BASE_URL = 'https://api.telegram.org/bot%s/' % self.TOKEN
        self.KEY = cache.create_key('telegram-chat-ids')

    @property
    def TOKEN(self):
        return self.__TOKEN

    @TOKEN.setter
    def TOKEN(self, value):
        raise MyFlaskException('Not allowed.')

    def send(self, sender, text, parse_mode=None, disable_web_page_preview=False,
                    disable_notification=False, reply_to_message_id=None, reply_markup=None):
        chat_id = self.get_chat_id()
        if chat_id is not 0:
            url = ud.Url(self.BASE_URL + 'sendMessage')
            message = {
                'chat_id': chat_id,
                'text': '{}: {}'.format(sender, text) if sender else text,
                'parse_mode': parse_mode or '',
                'disable_web_page_preview': disable_web_page_preview,
                'disable_notification': disable_notification,
                'reply_to_message_id': reply_to_message_id or '',
                'reply_markup': reply_markup or '',
            }
            response = self.fetch(url, payload=message, method='JSON', forced_update=True)
            return self.handle_response(response)

    def handle_response(self, response):
        js = json.loads(response.content)
        if not js.get('ok', False):
            log.warning('Telegram responded : %s', js)
            return False
        return js


    def update(self):
        if self.TOKEN is None:
            log.warning('Telegram bot token wasn\'t set.')
            return
        url = ud.Url(self.BASE_URL + 'getUpdates')
        js = self.handle_response(self.fetch(url, forced_update=True))
        if js:
            result = js.get('result')
            if len(result) > 0:
                chat_id = js.get('result')[0]['message']['chat']['id']
                cache.set(self.KEY, str(chat_id), timeout=0)
            else:
                log.warning('There is no message to update. You should send a new message to bot.')

    def get_chat_id(self):
        chat_id = 0
        for _ in range(2):
            cached = cache.get(self.KEY)
            if cached is not None:
                chat_id = int(cached)
                break
            else:
                self.update()
        return chat_id
