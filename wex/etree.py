""" Factory functions for extracting from lxml element trees. """

from __future__ import absolute_import, unicode_literals, print_function
import logging
from six.moves.urllib_parse import urljoin, quote, unquote
from functools import partial, wraps
from operator import is_, methodcaller

from six.moves import filter, reduce

from lxml.etree import XPath, _ElementTree, Element
from lxml.cssselect import CSSSelector
from lxml.html import HTMLParser, XHTML_NAMESPACE

from .composed import composable
from .cache import cached

SKIP = object()
skip = partial(is_, SKIP)

UNPARSEABLE = Element('unparseable')

base_href = XPath('//base[@href]/@href | //x:base[@href]/@href',
                  namespaces={'x': XHTML_NAMESPACE})

space_join = composable(' '.join)


default_namespaces = {'re': 'http://exslt.org/regular-expressions'}


class WrapsShim(object):

    def __init__(self, wrapped):
        self.wrapped = wrapped
        self.assignments = {
            '__module__': __name__,
            '__name__': repr(wrapped),
        }

    def __getattr__(self, attr):
        return getattr(self.wrapped, attr, self.assignments[attr])


@composable
@cached
def parse(src):
    if not hasattr(src, 'read'):
        return src
    charset = src.headers.get_content_charset()
    etree = _ElementTree()
    # if charset is not specified in the Content-Type, this will be
    # None ; encoding=None produces default (ISO 8859-1) behavior.
    parser = HTMLParser(encoding=charset)
    try:
        # Sometimes we get URLs containing characters that aren't
        # acceptable to lxml (e.g. "http:/foo.com/bar?this=array[]").
        # When this happens lxml will quote the whole URL.
        # We don't want to have to check for this so we just always
        # quote it here and then unquote it in the `base_url` function.
        quoted_base_url = quote(src.url) if src.url else src.url
        etree.parse(src, parser=parser, base_url=quoted_base_url)
    except IOError as exc:
        logging.getLogger(__name__).warning("IOError parsing %s (%s)", src.url, exc)
    root = etree.getroot()
    if root is None:
        etree._setroot(UNPARSEABLE)
    return etree


@cached
def base_url(root):
    unquoted_base_url = (unquote(root.base_url) if root.base_url
                                                else root.base_url)
    return reduce(urljoin, base_href(root)[:1], unquoted_base_url)


def css(expression):
    return parse | CSSSelector(expression)


def xpath(expression, namespaces=default_namespaces):
    return parse | XPath(expression, namespaces=namespaces)

def maybe_list(f):
    #@wraps(WrapsShim(f))
    def wrapper(src, *args, **kwargs):
        cache = {}
        if isinstance(src, list):
            return [ret for ret in (f(i) for i in src) if not skip(ret)]
        return f(src, __maybe_list_cache__=cache)
    return wrapper


def attrib(name, default=SKIP):
    return maybe_list(methodcaller('get', name, default))




def base_url_join(f):
    #@wraps(WrapsShim(f))
    def wrapper(src, *args, **kwargs):
        roottree = src.getroottree() if hasattr(src, 'getroottree') else src
        root = roottree.getroot()
        url = f(src)
        # urljoin requires 'find' so give up if we don't find it (e.g. None)
        if hasattr(url, 'find'):
            return urljoin(base_url(root), url)
        return url
    return wrapper


href = maybe_list(base_url_join(methodcaller('get', 'href', SKIP)))
src = maybe_list(base_url_join(methodcaller('get', 'src', SKIP)))


@composable
@maybe_list
def normalize_space(string, __maybe_list_cache__={}):
    return space_join(string.split())


def list_filter_join(src):
    """ Filters empty strings from a list """
    if isinstance(src, list):
        return ' '.join(filter(None, src))
    return src


@composable
@maybe_list
def text_content(src, __maybe_list_cache__={}):
    if hasattr(src, 'text_content'):
        if hasattr(src.tag, '__call__'):
            # ummm - it's an HtmlComment of course
            return ''
        return src.text_content()
    return ''


text = text_content | normalize_space | list_filter_join
text_list = text_content | normalize_space | list
