"""
Composable functions for extracting data using 
`lxml <http://lxml.de/>`_.
"""

from __future__ import absolute_import, unicode_literals, print_function
import logging
import wex.py2compat ; assert wex.py2compat
from six import string_types
from six.moves.urllib_parse import urljoin, quote, unquote
from functools import partial
from operator import is_, methodcaller
import codecs

from six.moves import reduce

from lxml.etree import XPath, _ElementTree, Element
from lxml.cssselect import CSSSelector
from lxml.html import XHTML_NAMESPACE, HTMLParser

from .composed import composable
from .cache import cached
from .iterable import flatten, map_if_iter, filter_if_iter
from .ncr import replace_invalid_ncr

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


def create_html_parser(headers):

    charset = headers.get_content_charset()
    try:
        if charset and codecs.lookup(charset).name == 'iso8859-1':
            charset = 'windows-1252'
    except LookupError:
        pass

    # if charset is not specified in the Content-Type, this will be
    # None ; encoding=None produces default (ISO 8859-1) behavior.
    return HTMLParser(encoding=charset)


@composable
@cached
def parse(src):
    """ Returns an element tree create by `LXML <http://lxml.de/>`_. 
       :param src: A readable object such as a :class:`wex.response.Response`.
    """

    if not hasattr(src, 'read'):
        return src

    parser = create_html_parser(src.headers)
    etree = _ElementTree()
    try:
        # Sometimes we get URLs containing characters that aren't
        # acceptable to lxml (e.g. "http:/foo.com/bar?this=array[]").
        # When this happens lxml will quote the whole URL.
        # We don't want to have to check for this so we just always
        # quote it here and then unquote it in the `base_url` function.
        quoted_base_url = quote(src.url) if src.url else src.url
        fp = replace_invalid_ncr(src)
        etree.parse(fp, parser=parser, base_url=quoted_base_url)
    except IOError as exc:
        logger = logging.getLogger(__name__)
        logger.warning("IOError parsing %s (%s)", src.url, exc)

    root = etree.getroot()
    if root is None:
        etree._setroot(UNPARSEABLE)

    return etree


@cached
def get_base_url(root):
    if root.base_url:
        base_url = unquote(root.base_url)
    else:
        base_url = root.base_url
    return reduce(urljoin, base_href(root)[:1], base_url)


def css(expression):
    """ Returns a :func:`composable <wex.composed.composable>` callable that
        will select elements defined by a 
        `CSS selector <http://en.wikipedia.org/wiki/Cascading_Style_Sheets#Selector>`_ 
        expression.

        :param expression: The CSS selector expression.

        The callable returned accepts a :class:`wex.response.Response`, a
        list of elements or an individual element as an argument.
    """
    return parse | map_if_iter(CSSSelector(expression))


def xpath(expression, namespaces=default_namespaces):
    """ Returns :func:`composable <wex.composed.composable>` callable that will
        select elements defined by an 
        `XPath <http://en.wikipedia.org/wiki/XPath>`_ expression.

        :param expression: The XPath expression.
        :param namespaces: The namespaces.

        The callable returned accepts a :class:`wex.response.Response`, a
        list of elements or an individual element as an argument.

        For example:

        .. code-block:: pycon

            >>> from lxml.html import fromstring
            >>> tree = fromstring('<h1>Hello</h1>')
            >>> selector = xpath('//h1')

    """
    return parse | map_if_iter(XPath(expression, namespaces=namespaces))


def attrib(name, default=None):
    getter = methodcaller('get', name, default)
    mapper = map_if_iter(getter)
    return mapper


def join_to_base_url(url_getter, same_domain=True):
    def base_url_join(elem_or_tree, *args, **kwargs):
        if hasattr(elem_or_tree, 'getroottree'):
            tree = elem_or_tree.getroottree()
        else:
            tree = elem_or_tree
        base_url = get_base_url(tree.getroot())
        url = url_getter(elem_or_tree)
        # urljoin requires 'find' so give up if we don't find it (e.g. None)
        if hasattr(url, 'find'):
            joined_url = urljoin(base_url, url.strip())
            if (same_domain and 
                not joined_url.startswith(urljoin(base_url, '/'))):
                return None
            return joined_url
        return url
    return map_if_iter(base_url_join) | filter_if_iter(None)


#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``href`` attribute as long as it is from the same domain
#: as the base URl of the response.
href_url = join_to_base_url(methodcaller('get', 'href'), same_domain=True)
#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``href`` attribute.
href_any_url = join_to_base_url(methodcaller('get', 'href'), same_domain=False)
#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``src`` attribute.
src_url = join_to_base_url(methodcaller('get', 'src'), same_domain=False)


@composable
def normalize_space(src):
    """ Return a whitespace normalized version of its input.

    :param src: text or iterable.

    If ``src`` is iterable then a generator will be returned.
    """
    if isinstance(src, string_types):
        return space_join(src.split())
    return (normalize_space_and_join(s) for s in src)


@composable
def normalize_space_and_join(src):
    """ Return a string of space-normalized text content. """
    if isinstance(src, string_types):
        return space_join(src.split())
    normalized = [normalize_space_and_join(s) for s in src]
    return space_join((s for s in normalized if s.strip()))


@composable
def itertext(src):
    """ Iterates text from elements.

        :param src: The element or elements to iterate.
    """
    if hasattr(src, 'itertext'):
        # using '*' to exclude comments
        return (t for t in src.itertext('*'))
    elif hasattr(src, '__iter__') and not isinstance(src, string_types):
        return (itertext(s) for s in src)
    return src


#: A :class:`wex.composed.ComposedFunction` that returns the whitespace 
#: normalized text from selected elements.
text = itertext | normalize_space

#: A :class:`wex.composed.ComposedCallable` that yields text nodes.
text_nodes = itertext | flatten

#: A :class:`wex.composed.ComposedFunction` that returns the whitespace 
#: normalized text from zero or more elements joined with a space.
join_text = itertext | normalize_space_and_join
