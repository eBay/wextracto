import requests
from six import iteritems
from six import BytesIO
from six.moves.urllib_parse import urljoin
from .py2compat import parse_headers
from .iterable import one
from .http import timeout, readable_from_response
from .etree import create_html_parser, get_base_url
from .response import Response


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
    def from_response(cls, response, url, decode_content):
        return cls(readable_from_response(response, url, decode_content))

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
            _, _, self.code, _ = Response.parse_status_line(line)
        self.lines.append(line)
        if not line.strip():
            self.headers = parse_headers(BytesIO(b''.join(self.lines[1:])))
            if 200 <= self.code < 300:
                self.parser = create_html_parser(self.headers)
        return line

    def close(self):
        self.readable.close()


def submit_form(url, method, session=None, **kw):

    if session is None:
        session = requests.Session()
        session.stream = True

    decode_content = kw.get('decode_content', True)

    response = session.request(
        'get',
        url,
        params=method.args.get('params', None),
        data=None,
        headers=method.args.get('headers', None),
        cookies=method.args.get('cookies', None),
        timeout=timeout,
        allow_redirects=False,
    )
    readable = ParserReadable.from_response(response, url, decode_content)
    yield readable

    redirects = session.resolve_redirects(response, response.request,
                                          stream=True, timeout=timeout)

    for response in redirects:
        readable = ParserReadable.from_response(response, url, decode_content)
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
        data = form.form_values()
        params = None
    else:
        data = None
        params = form.form_values()

    response = session.request(
        form_method,
        form_action_url,
        params=params,
        data=data,
        headers=method.args.get('headers', None),
        cookies=method.args.get('cookies', None),
        timeout=timeout,
        allow_redirects=False,
    )
    yield readable_from_response(response, url, decode_content)

    redirects = session.resolve_redirects(response, response.request,
                                          stream=True, timeout=timeout)
    for redirect in redirects:
        yield readable_from_response(redirect, url, decode_content)
