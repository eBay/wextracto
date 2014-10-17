from __future__ import unicode_literals, print_function
from six import BytesIO
from wex import output


def test_ensure_unicode():
    ustr = u'\xae'
    assert output.ensure_unicode(ustr) is ustr


def test_ensure_unicode_py2_str():
    ustr = u'\xae'
    assert output.ensure_unicode(ustr.encode('utf-8')) == ustr


def test_serialize_item():
    assert output.serialize_item(('a', 1)) == "a\t1\n"


def test_serialize_item_not_tuple():
    assert output.serialize_item('a') == '"a"\n'


def test_stdout_big_write_causes_flush():
    big_chunk = 'x' * (output.CHUNK_SIZE + 1)
    stdout = output.Stdout()
    stdout.stdout = BytesIO()
    stdout.write(big_chunk)
    assert len(stdout.stdout.getvalue()) == len(big_chunk)

response = b"""HTTP/1.1 200 OK

Hello
"""

def test_extract_to_stdout_saving_output_readable_has_no_name():
    def extractor(src):
        yield (1,)
    extract = output.ExtractToStdoutSavingOutput(extractor, '~/dontcare')
    readable = BytesIO(response)
    extract(readable)
