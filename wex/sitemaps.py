""" Extractors for URLs from 
`/robots.txt <http://en.wikipedia.org/wiki/Robots_exclusion_standard#Sitemap>`_
and `sitemaps <http://www.sitemaps.org/protocol.html>`_.
"""


from __future__ import unicode_literals, absolute_import, print_function
import logging
import wex.py2compat ; assert wex.py2compat
from lxml.etree import iterparse, XMLSyntaxError
from codecs import getreader
from six.moves.urllib_parse import urljoin
from wex.extractor import chained
from wex.http import decode
from wex.url import URL

log = logging.getLogger(__name__)


def urls_from_robots_txt(response):
    """ Yields sitemap URLs from "/robots.txt" """

    url = URL(response.request_url or response.url or '')
    if url.parsed.path != '/robots.txt':
        return

    charset = response.headers.get_content_charset()
    lines = getreader(charset or 'ISO-8859-1')(response)

    for line in lines:

        content, _, comment = line.partition('#')
        field, _, value = content.partition(':')
        if field.strip().lower() != 'sitemap':
            continue

        # we shouldn't need to urljoin but we do just in case
        joined = URL(urljoin(response.url, value.strip()))
        # set sitemap=True in fragment to help downstream processing
        yield "url", joined.update_fragment_dict(sitemap=True)


def urls_from_urlset_or_sitemapindex(response):
    """ Yields URLs from ``<urlset>`` or ``<sitemapindex>`` elements as per 
        `sitemaps.org <http://www.sitemaps.org/protocol.html>`_.
    """

    sitemap = URL(response.url).fragment_dict.get('sitemap')
    content_subtypes = response.headers.get_content_subtype().split('+')
    if not sitemap and 'xml' not in content_subtypes:
        return

    root = None
    try:
        for _, elem in iterparse(decode(response)):

            if root is None:
                root = elem.getroottree().getroot()
                if not (root.tag.endswith('}sitemapindex') or
                        root.tag.endswith('}urlset')):
                    # root element has wrong tag - give up
                    break

            if elem.tag.endswith('}loc') and elem.text is not None:
                text = elem.text.strip()
                if text:
                    # http://www.sitemaps.org/protocol.html#locdef
                    url = URL(urljoin(response.url, text))
                    if elem.getparent().tag.endswith('}sitemap'):
                        # set sitemap=True to help downstream processing
                        url = url.update_fragment_dict(sitemap=True)
                    yield "url", url

            if elem.getparent() is root:
                # release memory for previous elements
                while elem.getprevious() is not None:
                    del root[0]

    except XMLSyntaxError:
        log.debug("XMLSyntaxError in '%s' (%d)", response.url, response.code)

#: Extractor that combines :func:`.urls_from_robots_txt` and
#: :func:`.urls_from_urlset_or_sitemapindex`.
urls_from_sitemaps = chained(urls_from_robots_txt,
                             urls_from_urlset_or_sitemapindex)
