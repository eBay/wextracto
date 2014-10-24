import io
import posixpath
from functools import wraps
from ftplib import FTP
from .http import format_status_line, format_header, CRLF
from .readable import ChainedReadable


def get(url, recipe, **kw):
    """ Recipe for an FTP get. """
    timeout = kw.get('timeout', 10.0)
    ftp = FTP(url.parsed.hostname, url.parsed.username,
              url.parsed.password, timeout=timeout)
    dirname, basename = posixpath.split(url.parsed.path)
    ftp.cwd(dirname)
    return (_readable(url, RETRReadable(ftp, basename)),)


def close_on_empty(unbound):
    """ Calls 'close' on first argument when `method` return something falsey.

    The first argument is presumed to the `self`.
    """
    @wraps(unbound)
    def wrapper(self, *args):
        buf = unbound(self, *args)
        if not buf:
            self.close()
        return buf
    return wrapper


class RETRReadable(object):
    """ Just like ftplib.FTP.retrbinary, but implements read and readline. """

    def __init__(self, ftp, basename):
        self.ftp = ftp
        self.ftp.voidcmd('TYPE I')
        self.conn = ftp.transfercmd('RETR {}'.format(basename))
        self.fp = self.conn.makefile('rb')

    @close_on_empty
    def read(self, *args):
        return self.fp.read(*args)

    @close_on_empty
    def readline(self, *args):
        return self.fp.readline(*args)

    def close(self):
        self.fp.close()
        self.conn.close()
        self.ftp.voidresp()


def _readable(url, fp, **kw):
    """ Make an object that is readable by `Response`.from_file. """

    headers = io.TextIOWrapper(io.BytesIO(), encoding='utf-8', newline='\n')
    protocol = 'FTP'
    version = '1.0'
    code = 200
    reason = 'OK'
    status_line = format_status_line(protocol, version, code, reason)
    headers.write(status_line)
    headers.write(format_header('X-wex-url', url))
    headers.write(CRLF)
    headers.seek(0)

    return ChainedReadable(headers.detach(), fp)

