# coding=utf-8
from __future__ import unicode_literals
import codecs
from pkg_resources import resource_stream
import pytest
from six import text_type
from wex.response import Response
from wex.htmlstream import HTMLStream


def stream_from_fixture(fixture):
    resource = 'fixtures/htmlstream/' + fixture
    readable = resource_stream(__name__, resource)
    response = Response.from_readable(readable)
    stream = HTMLStream(response)
    return stream


def test_htmlstream():
    stream = stream_from_fixture('ascii')
    assert stream.declared_encodings == []
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<p>just ASCII</p>\n'


def test_htmlstream_unicode():
    stream = stream_from_fixture('utf-8')
    assert stream.declared_encodings == []
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<p>©<p>\n'


def test_htmlstream_utf8_bom():
    stream = stream_from_fixture('utf-8-with-bom')
    assert stream.declared_encodings == [('bom', 'utf-8')]
    assert stream.bom == codecs.BOM_UTF8
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<p>©<p>\n'


def test_htmlstream_utf16_le_bom():
    stream = stream_from_fixture('utf-16-le-with-bom')
    assert stream.declared_encodings == [('bom', 'utf-16-le')]
    assert stream.bom == codecs.BOM_UTF16_LE
    text = stream.read()
    assert stream.encoding == 'utf-16-le'
    assert isinstance(text, text_type)
    assert text == 'Hello'


def test_htmlstream_meta_charset():
    stream = stream_from_fixture('shift-jis-meta-charset')
    assert stream.declared_encodings == [('http-content-type', 'ISO-8859-1'),
                                         ('meta-charset', 'shift-jis')]
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<meta charset="shift-jis">\n<p>巨<p>\n'


def test_htmlstream_meta_http_equiv():
    stream = stream_from_fixture('shift-jis-meta-http-equiv')
    assert stream.declared_encodings == [('http-content-type', 'ISO-8859-1'),
                                         ('meta-content-type', 'shift-jis')]
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<meta http-equiv="content-type" content="text/html;charset=shift-jis">\n<p>巨<p>\n'  # flake8: noqa


def test_htmlstream_http_content_type():
    stream = stream_from_fixture('shift-jis-http-content-type')
    assert stream.declared_encodings == [('http-content-type', 'SHIFT-JIS'),
                                         ('meta-charset', 'iso-8859-1')]
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<meta charset="iso-8859-1">\n<p>巨<p>\n'


def test_htmlstream_next_encoding():
    stream = stream_from_fixture('shift-jis-next-decoder')
    assert stream.declared_encodings == [('http-content-type', 'SHIFT-JIS'),
                                         ('meta-charset', 'utf-8')]
    # HTMLStream likes the look of utf-8 in the <meta> charset
    # but the response is actually encoded in shift-jis so
    # this will raise a UnicodeDecodeError
    with pytest.raises(UnicodeDecodeError):
        stream.read()
    assert stream.encoding == 'utf-8'
    # now try the next encoding (shift-jis)
    stream.next_encoding()
    text = stream.read()
    assert stream.encoding == 'shift_jis'
    assert isinstance(text, text_type)
    assert text == '<meta charset="utf-8">\n<p>巨<p>\n'


def test_htmlstream_default_encoding():
    stream = stream_from_fixture('default')
    assert stream.declared_encodings == []
    # first default we try is utf-8
    with pytest.raises(UnicodeDecodeError):
        stream.read()
    # finally we try cp1252 with errors='replace'
    stream.next_encoding()
    text = stream.read()
    assert isinstance(text, text_type)
    assert text == '<p>�®</p>\n'
