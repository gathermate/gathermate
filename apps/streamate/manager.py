# -*- coding: utf-8 -*-

from apps.common.manager import Manager


def hire_manager(config):
    # type: (flask.config.Config, Text) -> Manager
    return StreamManager(config)


class StreamManager(Manager):

    def __init__(self, config):
        # type: (flask.config.Config) -> None
        super(StreamManager, self).__init__(config)
        self.__streamer_classes = self._register_modules('apps.streamate.streams', 'Streamer')

    def request(self, streamer, query):
        # type: (str, Type[Dict[str, Union[List[str], str]]]) -> ?
        try:
            streamer = self.__streamer_classes[streamer.capitalize()](self.config, query)
            return streamer.proxy()
        except KeyError:
            return "There is no streamer : %s" % streamer



