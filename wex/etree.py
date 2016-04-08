"""
Composable functions for extracting data using
`lxml <http://lxml.de/>`_.
"""

from __future__ import absolute_import, unicode_literals, print_function
import wex.py2compat ; assert wex.py2compat  # flake8: noqa
import logging
from itertools import islice, chain
from copy import deepcopy
from operator import methodcaller, itemgetter
from six import string_types, PY2
from six.moves import map, reduce
from six.moves.urllib_parse import urljoin, quote, unquote
from lxml.etree import (XPath,
                        _ElementTree,
                        _Element,
                        Element,
                        FunctionNamespace)
from lxml.cssselect import CSSSelector
from lxml.html import XHTML_NAMESPACE, HTMLParser

from .composed import composable, Composable
from .cache import cached
from .iterable import _do_not_iter_append, filter_if_iter
from .htmlstream import HTMLStream
from .ncr import replace_invalid_ncr
from .url import URL, public_suffix


if PY2:

    def quote_base_url(base_url):
        if isinstance(base_url, unicode):
            return quote(base_url.encode('utf-8'))
        return quote(base_url)

    def unquote_base_url(quoted):
        assert isinstance(quoted, unicode)
        quoted = quoted.encode('ascii')
        unquoted = unquote(quoted)
        return unquoted.decode('utf-8')

else:

    quote_base_url = quote
    unquote_base_url = unquote


NEWLINE = u'\n'
EMPTY = u''
SPACE = u' '





# we do not want to flatten etree elements
_do_not_iter_append(_Element)

UNPARSEABLE = Element('unparseable')

base_href = XPath('//base[@href]/@href | //x:base[@href]/@href',
                  namespaces={'x': XHTML_NAMESPACE})

default_namespaces = {'re': 'http://exslt.org/regular-expressions'}

# see http://lxml.de/extensions.html#the-functionnamespace
function_namespace = FunctionNamespace(None)

_html_text_nodes = XPath(
    'descendant-or-self::node()' +
    '[not(local-name()) or not(text())]' +
    '[not(ancestor::script or ancestor::style)]'
)


def _wex_html_text(context, arg=None):
    if arg is None:
        arg = [context.context_node]
    html_text = []
    for node in chain.from_iterable(map(_html_text_nodes, arg)):
        tag = getattr(node, 'tag', None)
        if tag is None:
            html_text.append(node)
        elif tag == 'br':
            html_text.append(NEWLINE)
        else:
            html_text.append(EMPTY)
    return EMPTY.join(html_text)

function_namespace['wex-html-text'] = _wex_html_text



@composable
@cached
def parse(src):
    """ Returns an element tree create by `LXML <http://lxml.de/>`_.
       :param src: A readable object such as a :class:`wex.response.Response`.
    """

    if not hasattr(src, 'read'):
        return src

    etree = _ElementTree()
    try:
        stream = HTMLStream(src)
        # Sometimes we get URLs containing characters that aren't
        # acceptable to lxml (e.g. "http:/foo.com/bar?this=array[]").
        # When this happens lxml will quote the whole URL.
        # We don't want to have to check for this so we just always
        # quote it here and then unquote it in the `base_url` function.
        quoted_base_url = quote_base_url(src.url) if src.url else src.url
        while True:
            try:
                fp = replace_invalid_ncr(stream)
                # fp is a Unicode stream
                # The lxml FAQ tells us that it is inefficient to do this
                # http://lxml.de/FAQ.html#can-lxml-parse-from-file-objects-opened-in-unicode-text-mode
                # but actually it seems just fine as long as you tell the parser to use 'utf-8'!?
                parser = HTMLParser(encoding='utf-8')
                etree.parse(fp, parser=parser, base_url=quoted_base_url)
                break
            except UnicodeDecodeError as exc:
                stream.next_encoding()
    except IOError as exc:
        logger = logging.getLogger(__name__)
        logger.warning("IOError parsing %s (%s)", src.url, exc)

    root = etree.getroot()
    if root is None:
        etree._setroot(UNPARSEABLE)

    return etree


@cached
def get_base_url_from_root(root):
    if root.base_url:
        # see :func:`.parse` for why we need to unquote
        base_url = unquote_base_url(root.base_url)
    else:
        base_url = root.base_url
    return reduce(urljoin, base_href(root)[:1], base_url)


def get_base_url(elem_or_tree):
    if hasattr(elem_or_tree, 'getroottree'):
        tree = elem_or_tree.getroottree()
    else:
        # if it doesn't have getroottree() we presume it's a tree!
        tree = elem_or_tree
    return get_base_url_from_root(tree.getroot())


class map_if_list(Composable):

    def __init__(self, func):
        self.func = func

    def __repr__(self):
        return '%s(%r)' % (self.__class__, self.func)

    def __compose__(self):
        return (self,)

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], list):
            return [res for res in map(self.func, *args, **kwargs)]
        return self.func(*args, **kwargs)


def css(expression):
    """ Returns a :func:`composable <wex.composed.composable>` callable that
        will select elements defined by a
        `CSS selector <http://en.wikipedia.org/wiki/Cascading_Style_Sheets#Selector>`_
        expression.

        :param expression: The CSS selector expression.

        The callable returned accepts a :class:`wex.response.Response`, a
        list of elements or an individual element as an argument.
    """
    return parse | map_if_list(CSSSelector(expression))


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
    return parse | map_if_list(XPath(expression, namespaces=namespaces))


def attrib(name, default=None):
    getter = methodcaller('get', name, default)
    return map_if_list(getter)


def base_url_pair_getter(get_url):
    """ Returns a function for gettting a tuple of `(base_url, url)` when
        called with an etree `Element` or `ElementTree`.

        In the returned pair `base_url` is the value returned from
        `:func:get_base_url` on the etree `Element` or `ElementTree`.
        There second value is the value returned by calling the `get_url`
        on the same the same etree `Element` or `ElementTree`, joined to
        the `base_url` using `urljoin`.  This allows `get_url` to return
        a relative URL.
    """
    @composable
    def get_base_url_pair(elem_or_tree):
        base_url = get_base_url(elem_or_tree)
        url = get_url(elem_or_tree)
        if url:
            url = URL(urljoin(base_url, url.strip()))
        return (URL(base_url), url)
    return get_base_url_pair


def same_domain(url_pair):
    """ Return second url of pair if both are from same domain. """

    if not all(url_pair):
        return None

    base_url, url = map(URL, islice(url_pair, 2))
    if base_url.parsed[:2] == url.parsed[:2]:
        return url

    return None


def same_suffix(url_pair):
    """ Return second url of pair if both have the same public suffix. """

    if not all(url_pair):
        return None

    base_url, url = map(URL, islice(url_pair, 2))

    if url.parsed.hostname is None:
        return None

    base_suffix = public_suffix(base_url)
    dot_suffix = '.' + base_suffix
    dot_hostname = '.' + url.parsed.hostname
    if dot_hostname.endswith(dot_suffix):
        return url



src_base_url_pair = base_url_pair_getter(methodcaller('get', 'src'))
href_base_url_pair = base_url_pair_getter(methodcaller('get', 'href'))

# helpers that operate on exactly one element
src_url_1 = src_base_url_pair | itemgetter(1)
href_url_1 = href_base_url_pair | same_domain
href_url_same_suffix_1 = href_base_url_pair | same_suffix
href_any_url_1 = href_base_url_pair | itemgetter(1)


#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``href`` attribute as long as it is from the same domain
#: as the base URl of the response.
href_url = map_if_list(href_url_1) | filter_if_iter(bool)

#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``href`` attribute as long as it is from the same
#: `public suffix <https://publicsuffix.org/>`_
#: as the base URl of the response.
href_url_same_suffix = (map_if_list(href_url_same_suffix_1) |
                        filter_if_iter(bool))

#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``href`` attribute.
href_any_url = map_if_list(href_any_url_1) | filter_if_iter(bool)


#: A :class:`wex.composed.ComposedFunction` that returns the absolute
#: URL from an ``src`` attribute.
src_url = map_if_list(src_url_1) | filter_if_iter(bool)


def itertext(*tags, **kw):
    """ Return a function that will return an iterator for text.  """
    with_tail = kw.pop('with_tail', True)
    if kw:
        raise ValueError('unexpected keyword arguments %s' % kw.keys())

    @composable
    def _itertext(src):
        if hasattr(src, 'itertext'):
            return src.itertext(*tags, with_tail=with_tail)
        elif hasattr(src, '__iter__') and not isinstance(src, string_types):
            text_nodes = (_itertext(i) for i in src)
            return chain.from_iterable(text_nodes)
        raise ValueError("%r is not iterable" % src)
    return _itertext


def drop_tree(*selectors):
    """ Return a function that will remove trees selected by `selectors`. """

    @map_if_list
    def tree_dropper(src):
        copied = None
        for selector in selectors:
            selected = selector(copied if copied is not None else src)
            if selected and copied is None:
                copied = deepcopy(src)
                selected = selector(copied)
            for selection in selected:
                selection.drop_tree()
        return copied if copied is not None else src
    return tree_dropper


@map_if_list
def normalize_space(obj):
    """ Normalize space according to standard Python rules.

    The definition of what is space used in XPath's
    `normalize-space <http://www.w3.org/TR/xpath/#function-normalize-space>`_
    is a small subset of the characters defined as space in the
    `unicode <https://en.wikipedia.org/wiki/Whitespace_character#Unicode>`_
    rules that Python uses.
    """
    if hasattr(obj, 'split'):
        obj_as_text = obj
    else:
        obj_as_text = text_content(obj)
    return SPACE.join(obj_as_text.split())


def list2set(obj):
    if isinstance(obj, list):
        return set(obj)
    return obj


#: Return text content from an object (typically node-set) excluding from
#: content from within `<script>` or `<style>` elements.
text_content = xpath('wex-html-text(.)')


#: Alias for `normalize-space | list2set`
text = normalize_space | list2set
