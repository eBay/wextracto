from __future__ import unicode_literals, print_function
from six import BytesIO
from io import StringIO
from wex import output


def test_stdout_big_write_causes_flush():
    big_chunk = 'x' * (output.CHUNK_SIZE + 1)
    stdout = output.StdOut()
    stdout.stdout = StringIO()
    stdout.write(big_chunk)
    assert len(stdout.stdout.getvalue()) == len(big_chunk)

wexin = b"""HTTP/1.1 200 OK

Hello
"""

def test_extract_to_stdout_saving_output_readable_has_no_name():
    readable = BytesIO(wexin)
    def extract(src):
        yield 1
    ret = output.write_values_to_stdout_and_dir(extract, readable)
    assert ret is None
