"""
``Wextracto`` extraction output contains one, JSON encoded, value per line.
Each value may be prefixed by zero or more keys to identify the value.
"""

from __future__ import absolute_import, unicode_literals, print_function
import os
import errno
import sys
import logging; log = logging.getLogger(__name__)
import codecs
from multiprocessing import Lock
from contextlib import closing
from .response import Response
from .readable import EXT_WEXIN

EXT_WEXOUT = '.wexout'

CHUNK_SIZE = 2**8


lock = Lock()


class StdOut(object):

    if sys.stdout.encoding is None:
        stdout = codecs.getwriter('UTF-8')(sys.stdout)
    else:
        stdout = sys.stdout

    def __init__(self):
        self.buffer = []
        self.size = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.flush()

    def flush(self):
        chunk = ''.join(self.buffer)
        if chunk:
            with lock:
                self.stdout.write(chunk)
                self.stdout.flush()
        self.buffer = []
        self.size = 0

    def write(self, text):
        self.buffer.append(text)
        self.size += len(text)
        if self.size > CHUNK_SIZE:
            self.flush()



class TeeStdOut(object):

    def __init__(self, path):
        self.tee = codecs.open(path, 'w', 'UTF-8')
        self.stdout = None

    def __enter__(self):
        self.stdout = StdOut.stdout
        return self

    def __exit__(self, *exc_info):
        sys.stdout = self.stdout
        self.close()

    def close(self):
        self.tee.close()

    def write(self, chunk):
        for write in (self.stdout.write, self.tee.write):
            write(chunk)

    def flush(self):
        for flush in (self.stdout.flush, self.tee.flush):
            flush()


def write_values_to_stdout(extract, readable):

    ret = None
    try:

        with closing(readable), StdOut() as stdout:
            for value in Response.values_from_readable(extract, readable):
                stdout.write(value.text())

    except IOError as exc:

        if exc.errno == errno.EPIPE:
            ret = SystemExit(0)
        else:
            log.exception('reading %r', readable)
            ret = SystemExit(exc)

    except Exception as exc:

        log.exception('while extracting from %r', readable)
        ret = exc
        raise

    return ret


def write_values_to_stdout_and_dir(extract, readable):

    stem, ext = os.path.splitext(getattr(readable, 'name', ''))
    if stem and ext == EXT_WEXIN:
        path = stem + EXT_WEXOUT
        with TeeStdOut(path):
            return write_values_to_stdout(extract, readable)

    return write_values_to_stdout(extract, readable)
