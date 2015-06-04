"""
URL Labelling
^^^^^^^^^^^^^

The convention for Wextracto is that any URL that should be downloaded 
is has the left-most label ``url``.  For example::

        "url"\t"http://example.net/some/url"

Data Labelling
^^^^^^^^^^^^^^

If you are extracting multiple types of data (for example people and 
addresses) then a good labelling scheme is important.

It is a good idea to label the extracted values so that you can sort them
easily using the Unix :command:`sort` command.

An example of a labelling scheme that allows this would be::

    {type}\t{identifier}\t{attribute}\t{value}

So we might end up with output that look like this::

    "person"\t"http://example.net/person/1"\t"name"\t"Tom Bombadil"
    "person"\t"http://example.net/person/1"\t"email"\t"tom1@example.net"
    "address"\t"http://example.net/address/2"\t"city"\t"New York"
    "address"\t"http://example.net/address/2"\t"postal code"\t"10001"
    "person"\t"http://example.net/person/3"\t"name"\t"Jack Sprat"
    "person"\t"http://example.net/person/3"\t"email"\t"jack3@example.net"
    "address"\t"http://example.net/address/4"\t"city"\t"London"
    "address"\t"http://example.net/address/4"\t"postal code"\t"E14 5AB"

With output like this we can easily sort and group it.
"""

from __future__ import absolute_import, unicode_literals, print_function
import os
import sys
import codecs
from six import PY3
from multiprocessing import Lock
from .readable import EXT_WEXIN

EXT_WEXOUT = '.wexout'

CHUNK_SIZE = 2**8


lock = Lock()


class StdOut(object):

    if PY3:
        # force 'utf-8' encoding on stdout
        stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    else:
        stdout = codecs.getwriter('utf-8')(sys.stdout)

    def __init__(self, readable):
        self.readable = readable
        self.buffer = []
        self.size = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.flush()
        self.close()

    def close(self):
        if hasattr(self.readable, 'close'):
            self.readable.close()

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



class TeeStdOut(StdOut):

    def __init__(self, readable):
        super(TeeStdOut, self).__init__(readable)
        stem, ext = os.path.splitext(getattr(readable, 'name', ''))
        if stem and ext == EXT_WEXIN:
            path = stem + EXT_WEXOUT
            self.tee = codecs.open(path, 'w', 'UTF-8')
        else:
            self.tee = None

    def close(self):
        super(TeeStdOut, self).close()
        if self.tee:
            self.tee.close()

    def write(self, chunk):
        super(TeeStdOut, self).write(chunk)
        if self.tee:
            self.tee.write(chunk)

    def flush(self):
        super(TeeStdOut, self).flush()
        if self.tee:
            self.tee.flush()
