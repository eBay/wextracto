""" Content Decoders HTTP

Ideally requests/urllib3 would do the decoding for us, but currently we
cannot rely on that because the `.raw.read()` can return b'' simply
because the decompressor doesn't have enough to work on.

See https://github.com/shazow/urllib3/issues/709

This is most of the work-around.  The other part is a small change
in wex/http.py
"""

from __future__ import unicode_literals
import io
import zlib

CHUNK = 1024 * 8


class ZDecoder(io.RawIOBase):
    """ Base class for HTTP content decoders based on zlib """

    def __init__(self, fp, z=None):
        self.fp = fp
        self.z = z
        self.flushed = None

    def readinto(self, buf):

        if self.z is None:
            self.z = zlib.decompressobj()
            retry = True
        else:
            retry = False

        n = 0
        max_length = len(buf)

        while max_length > 0:

            if self.flushed is None:

                chunk = self.fp.read(CHUNK)
                compressed = (self.z.unconsumed_tail + chunk)
                try:
                    decompressed = self.z.decompress(compressed, max_length)
                except zlib.error:
                    if not retry:
                        raise
                    self.z = zlib.decompressobj(-zlib.MAX_WBITS)
                    retry = False
                    decompressed = self.z.decompress(compressed, max_length)

                if not chunk:
                    self.flushed = self.z.flush()

            else:

                if not self.flushed:
                    return n

                decompressed = self.flushed[:max_length]
                self.flushed = self.flushed[max_length:]

            buf[n:n+len(decompressed)] = decompressed
            n += len(decompressed)
            max_length = len(buf) - n

        return n


class DeflateDecoder(ZDecoder):
    """ Decoding for "content-encoding: deflate" """


class GzipDecoder(ZDecoder):
    """ Decoding for "content-encoding: gzip" """

    def __init__(self, fp):
        ZDecoder.__init__(self, fp, zlib.decompressobj(16 + zlib.MAX_WBITS))
