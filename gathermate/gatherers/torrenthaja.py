# -*- coding: utf-8 -*-

import re
import logging as log

from lxml import etree

from gathermate.gatherer import Gatherer
from gathermate.exception import GathermateException as GE
from util import urldealer as ud
from util import toolbox as tb

def register():
    return 'Gatherer'

class Torrenthaja(Gatherer):
    URL = u'https://torrenthaja.com/'
    LIST_URL = ud.join(URL, '/bbs/board.php?bo_table=%s')
    SEARCH_QUERY = u'sca=&sop=and&sfl=wr_subject&stx=%s'
    PAGE_QUERY = u'page=%d'
    ID_REGEXP = re.compile(r'(\d{2,8})\.html')


    def get_list(self, r):
        # type: (fetchers.Response) -> Generator
        root = self.etree(r, encoding=self.encoding)

        list_xpath = r'//div[contains(@class, "td-subject")]/a'
        for e in root.xpath(list_xpath):
            try:
                link = e.get('href')
                id_ = self.get_id_num(link)
                if id_:
                    title = e.xpath('string()').strip()
                    tr = e.getparent().getparent().getparent()
                    date = tr.find('td[4]').text.strip()
                    size = tr.find('td[3]').text.strip()
                    etc = '{} {}'.format(size, date)
                    yield {'id': id_, 'title': title, 'link': link, 'etc': etc}
            except:
                GE.trace_error()

    def get_item(self, r):
        # type: (fetchers.Response) -> Generator
        root = self.etree(r, encoding=self.encoding)

        form_xpath = r'//form[contains(@action, "download.php")]'
        for e in root.xpath(form_xpath):
            try:
                ticket = {}
                link = e.get('action')
                ticket['method'] = e.get('method')
                inputs = e.findall('.//input')
                payload = {}
                for inpt in inputs:
                    payload[inpt.get('name')] = inpt.get('value')
                ticket['payload'] = ud.unsplit_qs(payload)
                th = e.find('.//th[@class="title"]')
                try:
                    fname = u'{}.torrent'.format(th.text.strip())
                except:
                    GE.trace_error()
                    log.debug(etree.tostring(th))
                    protected = th[0].get('data-cfemail')
                    if protected:
                        fname = u'{}{}.torrent'.format(tb.cf_decode(protected), th[0].tail)

                yield {'name': fname, 'link': link, 'type': 'file', 'ticket': ticket}
            except:
                GE.trace_error()

        magnet_xpath = r'//button[contains(@onclick, "magnet_link")]'
        magnet_regex = re.compile(r'magnet_link\(\'(.*)\'\);')
        for idx, e in enumerate(root.xpath(magnet_xpath)):
            try:
                onclick = e.get('onclick')
                magnet_name = root.xpath(r'{}/ancestor::table//th[@class="title"]'.format(magnet_xpath))[idx].text
                link = u'magnet:?xt=urn:btih:{}'.format(magnet_regex.search(onclick).group(1))
                if not magnet_name:
                    magnet_name = link
                yield {'name': magnet_name, 'link': link, 'type': 'magnet'}
            except:
                GE.trace_error()

        attached_xpath = r'//a[contains(@class, "view_file_download")]'
        for e in root.xpath(attached_xpath):
            try:
                fname = e[0].text
                flink = e.get('href')
                yield {'name': fname, 'link': flink, 'type': 'file'}
            except:
                GE.trace_error()

    def get_file(self, url, ticket):
        # type: (urldealer.Url, Dict[Text, object]) -> fetchers.Response
        payload = ticket.get('payload', None)
        method = ticket.get('method', 'GET')
        if payload:
            payload = ud.split_qs(payload)
        return self.fetch(url,
                          referer=ticket['referer'],
                          method=method,
                          payload=payload)

