"""
Functions creating readable objects.

These objects are readable because they have `readline` and `read` methods.
They are used to to create `Response` objects using `Response.from_readable`.
"""

from __future__ import absolute_import, unicode_literals, print_function
import os
import errno
import sys
import tarfile
from io import FileIO
from threading import local
from functools import partial as partial_
from contextlib import closing
from six import PY2
from . import py2compat
assert py2compat
from .url import URL


EXT_WEXIN = '.wexin'
LF = b'\n'


class partial(partial_):
    def __repr__(self):
        """ Customized __repr__ for use with `Open` class. """
        return '%r, %r' % (self.func, self.args)


class Open(object):
    """ Lazily open a readable, when asked for read/readline.

    The reason we want to lazily open the readable is because
    that makes this object pickleable in its pre-opened state
    and that allows us to send the readable into a
    `multiprocessing.Pool`.
    """

    def __init__(self, open):
        self.open = open

    def __repr__(self):
        return 'Open(%r)' % self.open

    def __getattr__(self, name):
        if name not in ('readline', 'read', 'close', 'name'):
            raise AttributeError
        fp = self.open()

        self.__dict__['read'] = fp.read
        self.__dict__['readline'] = fp.readline
        self.__dict__['close'] = fp.close
        if hasattr(fp, 'name'):
            self.__dict__['name'] = fp.name

        assert name in self.__dict__
        return self.__dict__[name]

_open_tarfile = local()
_open_tarfile.tarfile = None


def tarfile_open(path):
    tarfileobj = getattr(_open_tarfile, 'tarfile', None)
    if tarfileobj is not None:
        if tarfileobj.name == path and not tarfileobj.closed:
            # same tarfile - no need to re-open
            return tarfileobj
        # there shouldn't be any problem closing this
        # because the fact that we have been asked to
        # open another tarfile will always mean that this
        # process has moved on to a different file.
        tarfileobj.close()

    _open_tarfile.tarfile = tarfile.open(path, 'r')
    return _open_tarfile.tarfile


def tarfile_tarinfo_open(path, tarinfo):
    tf = tarfile_open(path)
    return tf.extractfile(tarinfo)


def readables_from_paths(paths, save_dir=None):
    """ Yield readables from a sequence of paths """

    for path in paths:
        if path.strip() == b'-':
            stdin = sys.stdin if PY2 else sys.stdin.buffer
            tar = tarfile.open(mode='r|*', fileobj=stdin)
            for member in tar:
                yield tar.extractfile(member)
        elif not os.path.exists(path) and URL(path).parsed.scheme:
            url = URL(path)
            readables = url.get()
            if save_dir:
                readables = save_readables(url, save_dir, readables)
            for readable in readables:
                yield readable
        else:
            for readable in readables_from_file_path(path):
                yield readable


def save_readables(url, save_dir, readables):
    url_dir = url.mkdirs(save_dir)
    for i, readable in enumerate(readables):
        basename = '{}{}'.format(i, EXT_WEXIN)
        path = os.path.join(url_dir, basename)
        fp = FileIO(path, 'w')
        readable = TeeReadable(readable, fp)
        with closing(readable):
            yield readable


def readables_from_file_path(path):
    """ Yield readables from a file system path """

    numdirs = 0
    for dirpath, dirnames, filenames in os.walk(path):
        numdirs += 1
        # Don't walk into "hidden" directories
        dirnames[:] = [n for n in dirnames if not n.startswith('.')]
        for filename in filenames:
            if filename.lower().endswith(EXT_WEXIN):
                filepath = os.path.join(dirpath, filename)
                yield Open(partial(FileIO, filepath))

    if numdirs < 1:
        if path.lower().endswith('EXT_WEXIN'):
            yield Open(partial(FileIO, path))
        else:
            try:
                tf = tarfile_open(path)
                for readable in readables_from_tarfile(tf):
                    yield readable
            except IOError as exc:
                if exc.errno != errno.ENOENT:
                    raise
                # we want to defer the ENOENT error to later
                # so we do that by yielding an Open(...)
                yield Open(partial(FileIO, path))
            except tarfile.ReadError:
                yield Open(partial(FileIO, path))


def readables_from_tarfile(tf):
    for ti in tf:
        if ti.name.endswith(EXT_WEXIN):
            yield Open(partial(tarfile_tarinfo_open, tf.name, ti))


class TeeReadable(object):
    """ Readable that writes out to a tee file. """

    def __init__(self, readable, tee):
        self.readable = readable
        self.tee = tee

    @property
    def name(self):
        return self.tee.name

    def read(self, size):
        buf = self.readable.read(size)
        if buf:
            self.tee.write(buf)
        return buf

    def readline(self, *args):
        buf = self.readable.readline(*args)
        if buf:
            self.tee.write(buf)
        return buf

    def close(self):
        if not getattr(self.readable, 'closed', False):
            # read remainder so tee gets everything
            chunk_size = 2**16
            while True:
                chunk = self.read(chunk_size)
                if not chunk:
                    break
        self.readable.close()
        self.tee.close()


class ChainedReadable(object):
    """ Readable that combines the contents of multiple filelike together """

    EMPTY = b''

    def __init__(self, *files):
        self.files = files
        self.n = 0

    def read(self, size):
        buf = self.EMPTY
        while len(buf) < size and self.n < len(self.files):
            chunk = self.files[self.n].read(size - len(buf))
            if not chunk:
                self.n += 1
            buf += chunk
        return buf

    def readline(self, *args):
        if self.n >= len(self.files):
            return self.EMPTY
        buf = self.files[self.n].readline(*args)
        while LF not in buf and (not args or len(buf) < args[0]):
            self.n += 1
            if self.n >= len(self.files):
                break
            # OK so this can end up reading a line > limit but it isn't
            # going to really matter so we just ignore the possibiity.
            # We don't want to have to manage remainders unless we have to.
            buf += self.files[self.n].readline(*args)
        return buf

    def close(self):
        for fileobj in self.files:
            fileobj.close()
