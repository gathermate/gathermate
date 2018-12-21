# -*- coding: utf-8 -*-
import traceback
import logging as log

from util import toolbox
from util.cache import cache


class GathermateException(Exception):

    def __init__(self, *args, **kwargs):
        # type: (*str, Optional[fetcher.Response]) -> None
        super(GathermateException, self).__init__(*args)
        self.response = kwargs.get('response', None)
        if self.response:
            if self.response.content:
                self.content = toolbox.decode(self.response.content)
            else:
                self.content = 'The response has no content.'
            cache.delete(self.response.key)

    @staticmethod
    def trace_error():
        # type: () -> None
        log.error('\n{}'.format(traceback.format_exc()))

    VIEW_ERROR_TEMPLATE = '''
        <i class="fa fa-exclamation-triangle" aria-hidden="true"></i> {{ msg }}
        {% if response %}
        <script>
          $(".view_response").off("click");
          $(".view_response").on("click", function(e){
            toggle($(this).children().first());
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
