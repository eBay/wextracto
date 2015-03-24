""" Functions for getting responses for HTTP urls. """

from __future__ import unicode_literals, print_function
import wex.py2compat ; assert wex.py2compat
import io
import requests
from gzip import GzipFile
from .readable import ChainedReadable


GZIP_MAGIC = b'\x1f\x8b'
CRLF = '\r\n'
timeout = 30.0


def request(url, method, session=None, **kw):
    """ Makes an HTTP request following redirects. """

    if session is None:
        session = requests.Session()
        session.stream = True

    decode_content = kw.get('decode_content', True)

    response = session.request(
        method.name,
        url,
        params=method.args.get('params', None),
        data=method.args.get('data', None),
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


def readable_from_response(response, url, decode_content=True):
    """ Make an object that is readable by `Response`.from_file. """

    headers = io.TextIOWrapper(io.BytesIO(), encoding='utf-8', newline='\n')
    protocol = 'HTTP'
    version = '{:.1f}'.format(response.raw.version / 10.0)
    code = response.status_code
    reason = response.reason
    status_line = format_status_line(protocol, version, code, reason)
    response.raw.decode_content = decode_content
    magic_bytes = response.raw.read(2)
    headers.write(status_line)
    for name, value in response.headers.items():
        headers.write(format_header(name.capitalize(), value))
    headers.write(format_header('X-wex-request-url', url))
    if response.url != url:
        # the URL for the response is not the same as the requested URL
        headers.write(format_header('X-wex-url', response.url))
    if magic_bytes == GZIP_MAGIC:
        headers.write(format_header('X-wex-has-gzip-magic', '1'))
    headers.write(CRLF)
    headers.seek(0)

    return ChainedReadable(headers.detach(), io.BytesIO(magic_bytes), response.raw)


def decode(src):
    content_encoding = src.headers.get('content-encoding', '')
    has_gzip_magic = (src.headers.get('X-wex-has-gzip-magic', '0') == '1')
    gzip = (
        src.headers.get_content_subtype() == 'x-gzip' or
        content_encoding == 'x-gzip' or
        (content_encoding == 'gzip' and has_gzip_magic)
    )
    if gzip:
        src.seek(0)
        return GzipFile(fileobj=src.fp, mode='rb')
    return src


format_status_line = '{}/{} {} {}\r\n'.format
format_header = '{}: {}\r\n'.format
