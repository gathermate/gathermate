# -*- coding: utf-8 -*-
import logging

from lxml.builder import E
from lxml import etree

from apps.gathermate.gatherer import Gatherer
from apps.common.exceptions import MyFlaskException

log = logging.getLogger(__name__)

def register():
    return 'Gatherer', Quotes

class Quotes(Gatherer):
    URL = 'http://quotes.toscrape.com/'
    encoding = 'utf-8'

    def get_page(self, r):

        root = self.etree(r, encoding=self.encoding)
        quotes = root.xpath('//div[@class="quote"]')


        html = E.html()
        body = E.body()
        html.append(body)

        for quote in quotes:
            try:
                author = quote.find('span/small').text
                text = quote.find('span[@class="text"]').text
                itemtype = quote.get('itemtype')
                link = quote.find(r'span/a').get('href')
                tags = [a.text for a in quote.findall('div/a[@class="tag"]')]
                body.append(E.p(
                    u'text: {}'.format(text),
                    E.br,
                    u'author: {}'.format(author),
                    E.br,
                    u'itemtype: {}, link: {}'.format(itemtype, link),
                    E.br,
                    u'tags: {}'.format(', '.join(tags))
                    )
                )

            except:
                MyFlaskException.trace_error()

        return etree.tostring(html, pretty_print=True,)