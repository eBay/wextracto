import os
import errno
import json
import logging
from operator import attrgetter, methodcaller
from hashlib import md5
from contextlib import contextmanager
from six import text_type, binary_type, string_types, next
from six.moves import filter
from six.moves.urllib_parse import (urlparse,
                                    urlunparse,
                                    parse_qs,
                                    parse_qsl,
                                    urlencode,
                                    unquote)
from pkg_resources import iter_entry_points
from publicsuffix import PublicSuffixList

from .py2compat import urlquote
from .composed import composable
from .iterable import map_if_iter
from .value import encode_json

logger = logging.getLogger(__name__)


DEFAULT_METHOD = 'get'

if hasattr(os, 'pathconf'):
    PC_NAME_MAX = os.pathconf(os.path.dirname(__file__), 'PC_NAME_MAX')
else:
    PC_NAME_MAX = 255  # pragma: no cover


@contextmanager
def eexist_is_ok():
    try:
        yield
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise


class Method(object):
    """ Method objects 'get' responses from a url.

        The Method object looks-up the correct implementation based on its
        name and the scheme of the url.

        The default method name is 'get'. Other method names can be specified
        in the fragment of the url.
    """
    def __init__(self, scheme, name, args=None):
        self.scheme = scheme
        self.name = name
        self.args = args or {}

    @property
    def group(self):
        return 'wex.method.{}'.format(self.scheme)

    def get(self, url, **kw):
        """ Get responses for 'url'. """
        entry_points = iter_entry_points(self.group, self.name)
        try:
            ep = next(entry_points)
        except StopIteration:
            raise ValueError("Missing method '%s' in '%s'" %
                             (self.name, self.group))
        method = ep.load()
        return method(url, self, **kw)


class URL(text_type):
    """ URL objects. """

    def __new__(cls, urlstring):
        if isinstance(urlstring, binary_type):
            # here we make a safe-ish assumption it is  a utf-8 string
            urlstring = urlstring.decode('utf-8')
        url = super(URL, cls).__new__(cls, urlstring)
        url.parsed = urlparse(url)
        return url


    @property
    def fragment_dict(self):
        """ Client side data dict represented as JSON in the fragment. """
        if not self.parsed.fragment:
            return {}

        if self.parsed.fragment.startswith('%7B'):
            fragment = unquote(self.parsed.fragment)
        elif not self.parsed.fragment.startswith('{'):
            return {}
        else:
            fragment = self.parsed.fragment

        try:
            data = json.loads(fragment)
            if not isinstance(data, dict):
                data = {}
        except ValueError as exc:
            logger.error("%s. Unable to parse %r", exc, fragment)
            data = {}

        return data

    def update_fragment_dict(self, **kw):
        fragment_dict = dict(self.fragment_dict)
        fragment_dict.update(kw)
        fragment = encode_json(fragment_dict)
        replaced = self.parsed._replace(fragment=fragment)
        return self.__class__(urlunparse(replaced))

    @property
    def method(self):
        """ The `Method` for this URL. """
        if not self.parsed.scheme:
            raise ValueError("URL has no scheme")

        method = self.fragment_dict.get('method', DEFAULT_METHOD)

        if isinstance(method, string_types):
            return Method(self.parsed.scheme, method, {})

        try:
            ((name, args),) = method.items()
        except:
            raise ValueError("invalid method %r" % method)
        return Method(self.parsed.scheme, name, args)

    def get(self, **kw):
        """ Get `url` using the appropriate `Method`. """
        return self.method.get(self, **kw)

    def mkdirs(self, top):
        dirpath = top
        for dirname in self.dirnames():
            dirpath = os.path.join(dirpath, dirname)
            with eexist_is_ok():
                os.mkdir(dirpath)
        return dirpath

    def dirnames(self):
        encoded = self.encode('utf-8')
        hexdigest = md5(encoded).hexdigest()
        names = [self.parsed.scheme, self.parsed.netloc]
        names.extend(filter(None, self.parsed.path.split('/')))
        if self.parsed.query:
            names.extend(self.parsed.query.split('&'))
        names.append(hexdigest)
        return [urlquote(name, safe='')[:PC_NAME_MAX] for name in names]


#
# URL related composable helpers
# ============================================================

public_suffix_list = PublicSuffixList()


@composable
@map_if_iter
def url(obj):
    return getattr(obj, 'url', obj)

parse_url = url | map_if_iter(urlparse)
url_query = parse_url | map_if_iter(attrgetter('query'))
url_path = parse_url | map_if_iter(attrgetter('path'))
url_hostname = parse_url | map_if_iter(attrgetter('hostname'))
url_query_dict = url_query | map_if_iter(parse_qs)
url_query_list = url_query | map_if_iter(parse_qsl)


def url_query_param(name, default=[]):
    return url_query_dict | map_if_iter(methodcaller('get', name, default))


def filter_url_query(*names, **kw):

    names = set(names)
    exclude = kw.pop('exclude', False)

    def included(pair):
        return pair[0] in names

    def excluded(pair):
        return pair[0] not in names

    if exclude:
        pred = excluded
    else:
        pred = included

    @composable
    @map_if_iter
    def url_query_filter(obj):
        parsed = parse_url(obj)
        qsl = list(filter(pred, parse_qsl(parsed.query)))
        filtered_query = urlencode(qsl)
        return urlunparse(parsed._replace(query=filtered_query))

    return url_query_filter


strip_url_query = filter_url_query()


@composable
@map_if_iter
def public_suffix(src):
    return public_suffix_list.get_public_suffix(url_hostname(src) or src)
