# -*- coding: utf-8 -*-
import traceback
import logging

from apps.common import toolbox
from apps.common import caching

log = logging.getLogger()

class GathermateException(Exception):

    def __init__(self, response=None, *args, **kwargs):
        if args:
            if len(args) > 1:
                self.message = args[0] % args[1:]
            else:
                self.message = args[0]
        for key, value in kwargs.iteritems():
            self.message += '\n{}: {}'.format(key, value)
        super(GathermateException, self).__init__(self.message)
        self.response = response
        if self.response is not None:
            if self.response.content:
                self.content = toolbox.decode(self.response.content)
            else:
                self.content = 'The response has no content.'
            if self.response.key is not None:
                caching.cache.delete(self.response.key)
            log.error('Status Code : %d, URL : %s', self.response.status_code, self.response.url)

    @staticmethod
    def trace_error():
        log.error('\n{}'.format(traceback.format_exc()))

    VIEW_ERROR_TEMPLATE = '''
        <i class="fa fa-exclamation-triangle" aria-hidden="true"></i> {{ msg }}
        {% if response %}
        <script>
          $(".view_response").off("click");
          $(".view_response").on("click", function(e){
            $(this).children().first().toggle();
          });
        </script>
        <div class="view_response" style="cursor:pointer;">
          >>Toggle Response<<
          <div style="display:none;">
            <pre>{{ response }}</pre>
          </div>
        </div>
        {% endif %}
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <script>
                        toastbar('{{ message }}');
                    </script>
                {% endfor %}
            {% endif %}
        {% endwith %}
    '''
