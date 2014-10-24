import os
import errno
import json
from operator import attrgetter, methodcaller
from hashlib import md5
from contextlib import contextmanager
from six import text_type, string_types, next
from six.moves import filter, filterfalse
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
def parse_url(obj, **kw):
    if hasattr(obj, 'url'):
        url = obj.url
    else:
        url = obj

    return urlparse(url)

query = parse_url | attrgetter('query')
path = parse_url | attrgetter('path')
hostname = parse_url | attrgetter('hostname')
params = query | parse_qs
param_list = query | parse_qsl


def param(name, default=[]):
    return params | methodcaller('get', name, default)


def filter_params(*names, **kw):

    names = set(names)
    filter_func = kw.get('filter_func', filter)

    def pred(param):
        return param[0] in names

    @composable
    def filter_params(obj):
        parsed = parse_url(obj)
        qsl = list(filter_func(pred, parse_qsl(parsed.query)))
        return urlunparse(parsed._replace(query=urlencode(qsl)))

    return filter_params


def remove_params(*names):
    return filter_params(*names, filter_func=filterfalse)


def whitelist_params(*names):
    return filter_params(*names)


strip_params = filter_params()


@composable
def public_suffix(src, **kw):
    return public_suffix_list.get_public_suffix(hostname(src) or src)
