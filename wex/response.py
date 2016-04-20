from __future__ import unicode_literals, print_function, absolute_import
from tempfile import SpooledTemporaryFile as SpooledTemporaryFile_
from shutil import copyfileobj
from six import PY2
from six.moves.urllib.response import addinfourl
from six.moves.http_client import BadStatusLine as _BadStatusLine
from .py2compat import parse_headers
from .cache import Cache
from .value import yield_values
from .iterable import _do_not_iter_append


DEFAULT_READ_SIZE = 2**16  # 64K
MAX_IN_MEMORY_SIZE = 2**29      # 512M
MAGIC_BYTES_LEN = 8


class BadStatusLine(_BadStatusLine):

    def __init__(self, line, readable):
        _BadStatusLine.__init__(self, line)
        self.args = line, readable


class Response(addinfourl):
    """ A urllib2 style Response with some extras.

        :param content: A file-like object containing the response content.
        :param headers: An HTTPMessage containing the response headers.
        :param url: The URL for which this is the response.
        :param code: The status code recieved with this response.
        :param protocol: The protocol received with this response.
        :param version: The protocol version received with this response.
        :param reason: The reason received with this response.
        :param request_url: The URL requested that led to this response.
    """

    def __init__(self, content, headers, url, code=None, **kw):
        addinfourl.__init__(self, content, headers, url, code)
        self.request_url = kw.pop('request_url', None)
        self.protocol = kw.pop('protocol', None)
        self.version = kw.pop('version', None)
        self.reason = kw.pop('reason', None)
        self.magic_bytes = kw.pop('magic_bytes', None)
        if kw:
            raise ValueError("unexpected keyword arguments %r" % kw.keys())

    def seek(self, offset=0, whence=0):
        """ Seek the content file position.

            :param int offset: The offset from whence.
            :param int whence: 0=from start,1=from current position,2=from end
        """
        self.fp.seek(offset, whence)
        return self.fp

    @classmethod
    def values_from_readable(cls, extractor, readable):
        response = cls.from_readable(readable)
        with Cache():
            for value in yield_values(extractor, response):
                yield value

    @classmethod
    def from_readable(cls, readable):

        status_line = readable.readline()

        if status_line.startswith(b'WARC/'):
            warc_protocol, warc_version = cls.parse_warc_version(readable,
                                                                 status_line)
            warc_headers = parse_headers(readable)

            # Now read the HTTP status line
            status_line = readable.readline()

        else:

            warc_headers = None

        protocol, version, code, reason = cls.parse_status_line(readable,
                                                                status_line)
        headers = parse_headers(readable)
        request_url = headers.get('X-wex-request-url')
        if request_url is None and warc_headers:
            request_url = warc_headers.get('WARC-target-uri')
        url = headers.get('X-wex-url', request_url)
        if PY2:
            if request_url is not None:
                request_url = request_url.decode('utf-8')
            if url is not None:
                url = url.decode('utf-8')
        magic_bytes, content = cls.content_file(readable, headers)
        return Response(content,
                        headers,
                        url,
                        code=code,
                        protocol=protocol.decode('utf-8'),
                        version=version,
                        reason=reason.decode('utf-8'),
                        request_url=request_url,
                        magic_bytes=magic_bytes)

    @staticmethod
    def parse_warc_version(readable, status_line):
        protocol, _, version = status_line.partition(b'/')
        # version is a tuple of integers
        try:
            version = tuple(map(int, version.split(b'.')))
        except ValueError:
            raise BadStatusLine(status_line, readable)
        return protocol, version

    @staticmethod
    def parse_status_line(readable, status_line=None, field_defaults=['']*3):
        if status_line is None:
            status_line = readable.readline()
        fields = status_line.rstrip(b'\r\n').split(None, 2) + field_defaults
        protocol_version, code, reason = fields[:3]

        # status code is always an integer
        if not code.isdigit():
            raise BadStatusLine(status_line, readable)
        code = int(code)

        protocol, _, version = protocol_version.partition(b'/')

        # version is a tuple of integers
        try:
            version = tuple(map(int, version.split(b'.')))
        except ValueError:
            raise BadStatusLine(status_line, readable)

        return protocol, version, code, reason

    @classmethod
    def content_file(cls, response_file, headers):
        content_file = SpooledTemporaryFile(max_size=MAX_IN_MEMORY_SIZE)
        magic_bytes = response_file.read(MAGIC_BYTES_LEN)
        content_file.write(magic_bytes)
        copyfileobj(response_file, content_file)
        content_file.seek(0)
        return magic_bytes, content_file


class SpooledTemporaryFile(SpooledTemporaryFile_):
    def read(self, size=None):
        return self._file.read() if size is None else self._file.read(size)


# Response supports __iter__ because that is normal for file-like objects
# but by default we don't want respones to be iterated when flattening or
# when composable helpers are trying to work out whether to map or not.
_do_not_iter_append(Response)
