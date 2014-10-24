from __future__ import unicode_literals, print_function, absolute_import
from tempfile import TemporaryFile
from shutil import copyfileobj
from io import BytesIO
from six import PY2
from six.moves.urllib.response import addinfourl
from six.moves.http_client import BadStatusLine
from .cache import Cache
from .value import yield_values


DEFAULT_READ_SIZE = 2**16  # 64K
MAX_IN_MEMORY_SIZE = 2**29      # 512M

if PY2:

    from httplib import HTTPMessage

    def parse_headers(fp):
        return HTTPMessage(fp, 0)

else:

    from http.client import parse_headers


class Response(addinfourl):
    """ Response class in the style of urllib2 with extra bits. """

    def __init__(self, fp, headers, **kw):
        wex_request_url = headers.get('x-wex-request-url', None)
        wex_url = headers.get('x-wex-url', wex_request_url)
        addinfourl.__init__(self, fp, headers,
                            kw.pop('url', wex_url),
                            kw.pop('code', None))
        self.protocol = kw.pop('protocol', None)
        self.version = kw.pop('version', None)
        self.reason = kw.pop('reason', None)
        self.request_url = kw.pop('request_url', wex_request_url)
        self.schedule = kw.pop('schedule', headers.get('x-wex-schedule', None))
        if kw:
            raise ValueError("unexpected keyword arguments %r" % kw.keys())

    def seek(self, pos=0, mode=0):
        self.fp.seek(pos, mode)
        return self.fp

    @classmethod
    def values_from_readable(cls, extract, readable):
        """ Yields values extracted from 'readable' using 'extract'. """
        response = cls.from_readable(readable)
        with Cache():
            for value in yield_values(extract, response):
                yield value

    @classmethod
    def from_readable(cls, readable, **kw):
        status_line = readable.readline()
        protocol, version, code, reason = cls.parse_status_line(status_line)
        headers = parse_headers(readable)
        content = cls.content_file(readable, headers)
        return Response(content, headers, protocol=protocol.decode('UTF-8'),
                                          version=version,
                                          code=code,
                                          reason=reason.decode('UTF-8'),
                                          **kw)

    @staticmethod
    def parse_status_line(status_line, field_defaults=['']*3):
        """ Parses HTTP style status line. """

        fields = status_line.rstrip(b'\r\n').split(None, 2) + field_defaults
        protocol_version, code, reason = fields[:3]

        # status code is always an integer
        if not code.isdigit():
            raise BadStatusLine(status_line)
        code = int(code)

        protocol, _, version = protocol_version.partition(b'/')

        # version is a tuple of integers
        try:
            version = tuple(map(int, version.split(b'.')))
        except ValueError:
            raise BadStatusLine(status_line)

        return protocol, version, code, reason

    @classmethod
    def content_file(cls, response_file, headers):

        try:
            content_length = int(headers.get('content-length', 0))
        except ValueError:
            content_length = 0

        size_with_content_length = min(content_length + 1, MAX_IN_MEMORY_SIZE)
        read_size = max(size_with_content_length, DEFAULT_READ_SIZE)
        buf = response_file.read(read_size)
        if len(buf) < read_size:
            # We've managed to read all the content in one go
            content_file = BytesIO(buf)
        else:
            content_file = TemporaryFile()
            content_file.write(buf)
            copyfileobj(response_file, content_file)
            content_file.seek(0)

        return content_file
