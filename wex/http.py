""" Functions for getting responses for HTTP urls. """

from __future__ import unicode_literals, print_function
import wex.py2compat ; assert wex.py2compat
import io
import requests
from six import PY2
from requests.sessions import merge_setting
from gzip import GzipFile
from .readable import ChainedReadable
from .http_decoder import DeflateDecoder, GzipDecoder


GZIP_MAGIC = b'\x1f\x8b'
CRLF = '\r\n'
timeout = 30.0



def request(url, method, session=None, **kw):
    """ Makes an HTTP request following redirects. """

    import os

    user_agent = os.environ.get('WEX_USER_AGENT')

    if session is None:
        session = requests.Session()
        session.stream = True
        session.headers = {'User-Agent': user_agent} if user_agent else None

    decode_content = kw.get('decode_content', True)
    proxies = kw.get('proxies', None)
    headers = merge_setting(method.args.get('headers'), kw.get('headers'))
    context = kw.get('context', {})
    auth = merge_setting(method.args.get('auth'), kw.get('auth'))

    response = session.request(
        method.name,
        url,
        allow_redirects=False,
        cookies=method.args.get('cookies', None),
        data=method.args.get('data', None),
        headers=headers,
        params=method.args.get('params', None),
        proxies=proxies,
        timeout=timeout,
        auth=auth,
    )
    yield readable_from_response(response, url, decode_content, context)

    redirects = session.resolve_redirects(response,
                                          response.request,
                                          proxies=proxies,
                                          stream=True,
                                          timeout=timeout)
    for redirect in redirects:
        yield readable_from_response(redirect, url, decode_content, context)


def readable_from_response(response, url, decode_content, context):
    """ Make an object that is readable by `Response`.from_file. """

    headers = io.TextIOWrapper(io.BytesIO(), encoding='utf-8', newline='\n')

    protocol = 'HTTP'
    version = '{:.1f}'.format(response.raw.version / 10.0)
    code = response.status_code
    reason = response.reason
    status_line = format_status_line(protocol, version, code, reason)
    headers.write(status_line)

    for name, value in response.headers.items():

        # Strictly speaking headers should only be iso-8859-1
        # but we've got a good chance of detecting incorrect utf-8
        # and for most headers it won't matter as they will be
        # in the common ascii subset.

        if PY2:

            try:
                name = name.decode('utf-8')
            except UnicodeDecodeError:
                name = name.decode('iso-8859-1')

            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                value = value.decode('iso-8859-1')

        headers.write(format_header(name.capitalize(), value))

    headers.write(format_header('X-wex-request-url', url))

    if response.url != url:
        # the URL for the response is not the same as the requested URL
        headers.write(format_header('X-wex-url', response.url))
    for name, value in context.items():
        headers.write(format_header('X-wex-context-{}'.format(name), value))
    headers.write(CRLF)
    headers.seek(0)

    # switch off urllib3 content decoding
    response.raw.decode_content = False
    content_encoding = response.headers.get('content-encoding', '').lower()
    if decode_content and content_encoding == 'gzip':
        content = GzipDecoder(response.raw)
    elif decode_content and content_encoding == 'deflate':
        content = DeflateDecoder(response.raw)
    else:
        content = response.raw

    return ChainedReadable(headers.detach(), content)


def decode(src):
    content_encoding = src.headers.get('content-encoding', '')
    declared_as_gzip = (
        src.headers.get_content_subtype() == 'x-gzip' or
        content_encoding == 'x-gzip' or
        content_encoding == 'gzip'
    )
    has_gzip_magic = (src.magic_bytes[:2] == b'\037\213')
    if declared_as_gzip and has_gzip_magic:
        src.seek(0)
        return GzipFile(fileobj=src.fp, mode='rb')
    return src


format_status_line = '{}/{} {} {}\r\n'.format
format_header = '{}: {}\r\n'.format
