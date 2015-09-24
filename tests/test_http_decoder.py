import os
import zlib
from gzip import GzipFile
import pytest
from six import BytesIO
from wex.http_decoder import GzipDecoder, DeflateDecoder


def decode(uncompressed, compress, decoder_class):

    compressed = compress(uncompressed)
    decoder = decoder_class(compressed)

    # mimic the small/large read of wex.response:Response
    chunks = [
        decoder.read(8),
    ]

    while True:
        chunk = decoder.read(1024)
        if not chunk:
            break
        chunks.append(chunk)

    # Each chunk we read should match the corresponding parts
    # of the uncompressed data
    offset = 0
    for chunk in chunks:
        assert chunk == uncompressed[offset:offset+len(chunk)]
        offset += len(chunk)

    # and there should not be anything left unread
    assert uncompressed[offset:] == b''


def compress_with_gzip(uncompressed):
    compressed = BytesIO()
    with GzipFile(fileobj=compressed, mode='w') as gz:
        gz.write(uncompressed)
    compressed.seek(0)
    return compressed


def compress_with_deflate(uncompressed):
    deflate = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = deflate.compress(uncompressed) + deflate.flush()
    return BytesIO(compressed)


def test_gzip_decoder():
    uncompressed = os.urandom(1024 * 2)
    decode(uncompressed, compress_with_gzip, GzipDecoder)


def test_deflate_decoder():
    uncompressed = os.urandom(1024 * 2)
    decode(uncompressed, compress_with_deflate, DeflateDecoder)


def test_wrong_decoder():
    uncompressed = os.urandom(1024 * 2)
    with pytest.raises(zlib.error) as excinfo:
        decode(uncompressed, compress_with_deflate, GzipDecoder)
    assert excinfo.value.message.startswith('Error -3 ')
