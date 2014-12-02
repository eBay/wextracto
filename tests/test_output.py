from __future__ import unicode_literals, print_function
from six import BytesIO
from io import StringIO
from wex.output import (write_values,
                        StdOut,
                        TeeStdOut,
                        EXT_WEXIN,
                        EXT_WEXOUT,
                        CHUNK_SIZE)


def test_stdout_big_write_causes_flush():
    big_chunk = 'x' * (CHUNK_SIZE + 1)
    stdout = StdOut(None)
    stdout.stdout = StringIO()
    stdout.write(big_chunk)
    assert len(stdout.stdout.getvalue()) == len(big_chunk)

wexin = b"""HTTP/1.1 200 OK

Hello
"""


def test_write_values_tee_stdout(tmpdir):
    readable = BytesIO(wexin)
    readable.name = tmpdir.join('0' + EXT_WEXIN).strpath
    def extract(src):
        yield 1
    ret = write_values(TeeStdOut, readable, extract)
    assert ret is None
    with tmpdir.join('0' + EXT_WEXOUT).open() as fp:
        assert fp.read() == '1\n'


def test_write_values_tee_stdout_readable_has_no_name():
    readable = BytesIO(wexin)
    def extract(src):
        yield 1
    ret = write_values(TeeStdOut, readable, extract)
    assert ret is None
