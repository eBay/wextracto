import codecs
import requests
from six import iteritems
from six import BytesIO
from six.moves.urllib_parse import urljoin
from lxml.html import _nons, HTMLParser
from .py2compat import parse_headers
from .iterable import one
from .http import timeout, readable_from_response, merge_setting
from .etree import get_base_url
from .response import Response


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


class ParserReadable(object):
    """ Readable that feeds a parser as it is reads. """

    def __init__(self, readable):
        self.readable = readable
        self.lines = []
        self.code = None
        self.headers = None
        self.parser = None
        self.root = None

    @classmethod
    def from_response(cls, response, url, decode_content, context):
        return cls(readable_from_response(response, url,
                                          decode_content=decode_content,
                                          context=context))

    @property
    def name(self):
        return getattr(self.readable, 'name')

    def read(self, size):
        buf = self.readable.read(size)
        if self.parser:
            self.parser.feed(buf)
            if len(buf) < size:
                if self.root is None:
                    self.root = self.parser.close()
                    url = self.headers.get('X-wex-request-url')
                    # this sets the .base_url
                    self.root.getroottree().docinfo.URL = url
        return buf

    def readline(self, *args):
        line = self.readable.readline(*args)
        if not self.lines:
            _, _, self.code, _ = Response.parse_status_line(self.readable,
                                                            line)
        self.lines.append(line)
        if not line.strip():
            self.headers = parse_headers(BytesIO(b''.join(self.lines[1:])))
            if 200 <= self.code < 300:
                self.parser = create_html_parser(self.headers)
        return line

    def close(self):
        self.readable.close()


# just like:
# https://github.com/lxml/lxml/blob/master/src/lxml/html/__init__.py#L1004
# but doesn't ignore <input type="submit" ...> elements
def form_values(self):
    """
    Return a list of tuples of the field values for the form.
    This is suitable to be passed to ``urllib.urlencode()``.
    """
    results = []
    for el in self.inputs:
        name = el.name
        if not name:
            continue
        tag = _nons(el.tag)
        if tag == 'textarea':
            results.append((name, el.value))
        elif tag == 'select':
            value = el.value
            if el.multiple:
                for v in value:
                    results.append((name, v))
            elif value is not None:
                results.append((name, el.value))
        else:
            assert tag == 'input', (
                "Unexpected tag: %r" % el)
            if el.checkable and not el.checked:
                continue
            if el.type in ('image', 'reset'):
                continue
            value = el.value
            if value is not None:
                results.append((name, el.value))
    return results


def submit_form(url, method, session=None, **kw):

    if session is None:
        session = requests.Session()
        session.stream = True

    decode_content = kw.get('decode_content', True)
    proxies = kw.get('proxies', None)
    headers = merge_setting(method.args.get('headers'), kw.get('headers'))
    context = kw.get('context', {})
    auth = merge_setting(method.args.get('auth'), kw.get('auth'))

    response = session.request(
        'get',
        url,
        allow_redirects=False,
        cookies=method.args.get('cookies', None),
        data=None,
        headers=headers,
        params=method.args.get('params', None),
        proxies=proxies,
        timeout=timeout,
        auth=auth,
    )
    readable = ParserReadable.from_response(response, url,
                                            decode_content=decode_content,
                                            context=context)
    yield readable

    redirects = session.resolve_redirects(response,
                                          response.request,
                                          proxies=proxies,
                                          stream=True,
                                          timeout=timeout)

    for response in redirects:
        readable = ParserReadable.from_response(response, url,
                                                decode_content=decode_content,
                                                context=context)
        yield readable

    if readable.root is None:
        return

    form_css_selector, values = one(iteritems(method.args))
    form = one(readable.root.cssselect(form_css_selector))

    if isinstance(values, dict):
        values = values.items()

    for name, value in values:
        if name in form.inputs:
            input = form.inputs[name]
        else:
            input = one(form.cssselect(name))
        if hasattr(input, 'add'):
            input.add(value)
        else:
            input.value = value

    base_url = get_base_url(form)
    form_action_url = urljoin(base_url, form.get('action', ''))

    form_method = form.method.upper()
    if form_method in ('POST', 'PUT'):
        # this implies 'application/x-www-form-urlencoded'
        data = form_values(form)
        params = None
    else:
        data = None
        params = form_values(form)

    response = session.request(
        form_method,
        form_action_url,
        params=params,
        allow_redirects=False,
        cookies=method.args.get('cookies', None),
        data=data,
        headers=headers,
        proxies=proxies,
        timeout=timeout,
    )
    yield readable_from_response(response, url,
                                 decode_content=decode_content,
                                 context=context)

    redirects = session.resolve_redirects(response,
                                          response.request,
                                          proxies=proxies,
                                          stream=True,
                                          timeout=timeout)
    for redirect in redirects:
        yield readable_from_response(redirect, url,
                                     decode_content=decode_content,
                                     context=context)
