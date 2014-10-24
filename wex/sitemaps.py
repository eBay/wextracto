from __future__ import unicode_literals, absolute_import, print_function
import wex.py2compat ; assert wex.py2compat
from lxml.etree import iterparse
from codecs import getreader
from six.moves.urllib_parse import urljoin
from wex.http import decode
from wex.url import URL


def urls_from_robots_txt(src):
    """ Yields sitemap URLs from "/robots.txt" """
    src_url = URL(src.request_url or src.url or '')
    if src_url.parsed.path != '/robots.txt':
        return

    charset = src.headers.get_content_charset()
    lines = getreader(charset or 'ISO-8859-1')(src)

    for line in lines:

        content, _, comment = line.partition('#')
        field, _, value = content.partition(':')
        if field.strip().lower() != 'sitemap':
            continue

        url = URL(urljoin(src.url, value.strip()))

        yield "url", url.update_fragment(robots=True)


def urls_from_sitemap(src):

    robots = URL(src.request_url).fragment.get('robots')
    content_subtype = src.headers.get_content_subtype()
    xml_in_subtype = 'xml' in content_subtype.split('+')
    if not robots and not xml_in_subtype:
        return


    root = None
    for _, elem in iterparse(decode(src)):

        if root is None:
            root = elem.getroottree().getroot()
            if not (root.tag.endswith('}sitemapindex') or
                    root.tag.endswith('}urlset')):
                # root element has wrong tag - give up
                break

        if elem.tag.endswith('}loc') and elem.text is not None:
            text = elem.text.strip()
            if text:
                url = URL(urljoin(src.url, text))
                if elem.getparent().tag.endswith('}sitemap'):
                    url = url.update_fragment(robots=True)
                yield "url", url

        if elem.getparent() is root:
            # release memory for previous elements
            while elem.getprevious() is not None:
                del root[0]
