"""
The ``wex`` command output is a series of key,value pairs
where the value is JSON encoded.
"""

from __future__ import absolute_import, unicode_literals, print_function
import os
import errno
import sys
import json
import logging
from codecs import getwriter
from multiprocessing import Lock
from contextlib import contextmanager, closing
from six import PY2, binary_type
from six.moves import map
from .cache import ComposeCache
from .response import Response
from .readable import EXT_WEXIN

EXT_WEXOUT = '.wexout'

NL = '\n'
TAB = '\t'
CHUNK_SIZE = 2**8


encoder = json.JSONEncoder(
    skipkeys=False,
    ensure_ascii=False,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=(',', ':'),
    encoding='utf-8',
    default=None,
    sort_keys=True,
)
json_encode = encoder.encode


lock = Lock()
lines = []
write = sys.stdout


if PY2:
    def ensure_unicode(obj):
        if isinstance(obj, binary_type):
            return obj.decode('utf-8')
        return obj
else:  # pragma: no cover
    ensure_unicode = lambda u: u  # pragma: no cover


def serialize_item(item):
    """ Returns the serialized item in a string, ending with a newline. """
    if isinstance(item, tuple):
        key = tuple(map(ensure_unicode, item[:-1]))
        value = item[-1]
    else:
        key = ()
        value = item

    if isinstance(value, Exception):
        encoded_value = "###" + json_encode(unicode(value)) + "###"
    else:
        encoded_value = json_encode(value)

    return TAB.join(key + (encoded_value,)) + NL


class Stdout(object):

    stdout = None

    def __init__(self, fp=None):
        self.written = []
        self.bufsize = 0
        if sys.stdout.encoding is None:
            self.stdout = getwriter('utf-8')(sys.stdout)

    def flush(self):
        chunk = ''.join(self.written)
        stdout = self.stdout or sys.stdout
        if chunk:
            with lock:
                stdout.write(chunk)
                stdout.flush()
        self.written = []
        self.bufsize = 0

    def write(self, line):
        self.bufsize += len(line)
        self.written.append(line)
        if self.bufsize > CHUNK_SIZE:
            self.flush()


@contextmanager
def flushing(obj):
    try:
        yield obj
    finally:
        obj.flush()


stdout = Stdout()


class Tee(object):

    def __init__(self, stdout, path):
        self.stdout = stdout
        self.tee = open(path, 'w')

    def close(self):
        self.tee.close()

    def write(self, chunk):
        self.stdout.write(chunk)
        self.tee.write(chunk)

    def flush(self):
        self.stdout.flush()
        self.tee.flush()


class ExtractToStdout(object):

    def __init__(self, extractor):
        self.extractor = extractor

    def __call__(self, readable, dest=None):

        if dest is None:
            dest = stdout

        exc = None
        try:
            response = Response.from_readable(readable)
            with ComposeCache(), flushing(dest), closing(readable):
                for item in self.extractor(response):
                    dest.write(serialize_item(item))
        except IOError as exc:
            if exc.errno == errno.EPIPE:
                return SystemExit(0)
            logging.getLogger(__name__).exception('reading %r', readable)
            return SystemExit(exc)
        except Exception as exc:
            logging.getLogger(__name__).exception('reading %r', readable)

        return exc


class ExtractToStdoutSavingOutput(ExtractToStdout):

    def __init__(self, extractor, responses_dir):
        super(ExtractToStdoutSavingOutput, self).__init__(extractor)
        self.responses_dir = responses_dir

    def __call__(self, readable):
        stem, ext = os.path.splitext(getattr(readable, 'name', ''))
        if stem and ext == EXT_WEXIN:
            path = stem + EXT_WEXOUT
            dest = Tee(stdout, path)
            with closing(dest):
                return super(ExtractToStdoutSavingOutput, self).__call__(readable, dest)
        else:
            return super(ExtractToStdoutSavingOutput, self).__call__(readable)
