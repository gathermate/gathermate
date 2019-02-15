# -*- coding: utf-8 -*-

import json

from apps.common import fetchers
from apps.common.cache import cache

class Streamer(object):

    def fetch(self, url, **kwargs):
        return fetchers.hire_fetcher(config=self.config).fetch(url, cached=False, **kwargs)

    def get_cache(self):
        cached = cache.get(cache.create_key(self.CACHE_KEY))
        if cached is None:
            return {}
        return json.loads(str(cached))

    def set_cache(self, value, timeout=60):
        cache.set(cache.create_key(self.CACHE_KEY), json.dumps(value), timeout=timeout)

    def proxy(self):
        pass

