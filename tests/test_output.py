from __future__ import unicode_literals, print_function
from io import StringIO
from wex.output import StdOut, CHUNK_SIZE


def test_stdout_big_write_causes_flush():
    big_chunk = 'x' * (CHUNK_SIZE + 1)
    stdout = StdOut(None)
    stdout.stdout = StringIO()
    stdout.write(big_chunk)
    assert len(stdout.stdout.getvalue()) == len(big_chunk)
