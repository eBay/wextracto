import os
import errno
import json
from operator import attrgetter, methodcaller
from hashlib import md5
from contextlib import contextmanager
from six import text_type, string_types, next
from six.moves import filter
from six.moves.urllib_parse import (urlparse,
                                    urlunparse,
                                    parse_qs,
                                    parse_qsl,
                                    urlencode,
                                    unquote,
                                    quote)
from pkg_resources import iter_entry_points
from publicsuffix import PublicSuffixList

from .composed import composable
from .iterable import iterate, map_when
from .value import json_encode


DEFAULT_METHOD = 'get'
PC_NAME_MAX = os.pathconf(os.path.dirname(__file__), 'PC_NAME_MAX')


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
            raise ValueError("Missing method '%s' in '%s'" % (self.name, self.group))
        method = ep.load()
        return method(url, self, **kw)


class URL(text_type):
    """ URL objects. """

    def __new__(cls, urlstring):
        url = super(URL, cls).__new__(cls, urlstring)
        url.parsed = urlparse(url)
        return url


    @property
    def fragment(self):
        """ Client side data represented as JSON in the fragment. """
        if not self.parsed.fragment:
            return {}

        if self.parsed.fragment.startswith('%7B'):
            fragment = unquote(self.parsed.fragment)
        else:
            fragment = self.parsed.fragment

        try:
            return json.loads(fragment)
        except ValueError:
            pass
        return {}

    def update_fragment(self, **kw):
        fragment = dict(self.fragment)
        fragment.update(kw)
        fragment = json_encode(fragment)
        return self.__class__(urlunparse(self.parsed._replace(fragment=fragment)))

    @property
    def method(self):
        """ The `Method` for this URL. """
        if not self.parsed.scheme:
            raise ValueError("URL has no scheme")

        method = self.fragment.get('method', DEFAULT_METHOD)

        if isinstance(method, string_types):
            return Method(self.parsed.scheme, method, {})

        try:
            ((name, params),) = method.items()
        except:
            raise ValueError("invalid method %r" % method)
        return Method(self.parsed.scheme, name, params)

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
        hexdigest = md5(self.encode('utf-8')).hexdigest()
        names = [self.parsed.scheme, self.parsed.netloc]
        names.extend(self.parsed.path.split('/'))
        if self.parsed.query:
            names.extend(self.parsed.query.split('&'))
        names.append(hexdigest)
        return [quote(name, safe='')[:PC_NAME_MAX] for name in names]



#
# URL related composable helpers
#============================================================


public_suffix_list = PublicSuffixList()


@composable
def url_attr_1(obj):
    return getattr(obj, 'url', obj)

parse_url_1 = url_attr_1 | urlparse
parse_url = map_when(iterate)(parse_url_1)

url_query_1 = parse_url_1 | attrgetter('query')
url_query = map_when(iterate)(url_query_1)

url_path_1 = parse_url_1 | attrgetter('path')
url_path = map_when(iterate)(url_path_1)

url_hostname_1 = parse_url_1 | attrgetter('hostname')
url_hostname = map_when(iterate)(url_hostname_1)

url_query_dict_1 = url_query_1 | parse_qs
url_query_dict = map_when(iterate)(url_query_dict_1)

url_query_list_1 = url_query_1 | parse_qsl
url_query_list = map_when(iterate)(url_query_list_1)


def url_query_param_1(name, default=[]):
    return url_query_dict_1 | methodcaller('get', name, default)


def url_query_param(name, default=[]):
    return map_when(iterate)(url_query_param_1(name, default))


def filter_url_query_1(*names, **kw):

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
    def url_query_filter(obj):
        parsed = parse_url_1(obj)
        qsl = list(filter(pred, parse_qsl(parsed.query)))
        filtered_query = urlencode(qsl)
        return urlunparse(parsed._replace(query=filtered_query))

    return url_query_filter


def filter_url_query(*names, **kw):
    return map_when(iterate)(filter_url_query_1(*names, **kw))


strip_url_query = map_when(iterate)(filter_url_query_1())


@composable
@map_when(iterate)
def public_suffix(src):
    return public_suffix_list.get_public_suffix(url_hostname_1(src) or src)
