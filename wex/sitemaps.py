""" Extractors for URLs from 
`/robots.txt <http://en.wikipedia.org/wiki/Robots_exclusion_standard#Sitemap>`_
and `sitemaps <http://www.sitemaps.org/protocol.html>`_.
"""


from __future__ import unicode_literals, absolute_import, print_function
import wex.py2compat ; assert wex.py2compat
from lxml.etree import iterparse
from codecs import getreader
from six.moves.urllib_parse import urljoin
from wex.extractor import Chain
from wex.http import decode
from wex.url import URL


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

    content_subtype = response.headers.get_content_subtype()
    if 'xml' not in content_subtype.split('+'):
        return

    root = None
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
                # according to http://www.sitemaps.org/protocol.html#locdef
                # these 
                # this 
                url = URL(urljoin(response.url, text))
                if elem.getparent().tag.endswith('}sitemap'):
                    # add a sitemap=True to fragment so that
                    # in case we need to read an Atom, RSS or text file.
                    url = url.update_fragment_dict(sitemap=True)
                yield "url", url

        if elem.getparent() is root:
            # release memory for previous elements
            while elem.getprevious() is not None:
                del root[0]

#: Extractor that combines :func:`.urls_from_robots_txt` and
#: :func:`.urls_from_urlset_or_sitemapindex`.
urls_from_sitemaps = Chain(urls_from_robots_txt,
                           urls_from_urlset_or_sitemapindex)
