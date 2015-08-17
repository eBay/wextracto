# coding=utf-8
from __future__ import unicode_literals
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


def test_htmltream():
    s = stream_from_fixture('ascii').read()
    assert isinstance(s, text_type)
    assert s == '<p>just ASCII</p>\n'


def test_htmltream_unicode():
    s = stream_from_fixture('utf-8').read()
    assert isinstance(s, text_type)
    assert s == '<p>©<p>\n'


def test_htmltream_meta_charset():
    s = stream_from_fixture('shift-jis-meta-charset').read()
    assert isinstance(s, text_type)
    assert s == '<meta charset="shift-jis">\n<p>巨<p>\n'


def test_htmltream_meta_http_equiv():
    s = stream_from_fixture('shift-jis-meta-http-equiv').read()
    assert isinstance(s, text_type)
    assert s == '<meta http-equiv="content-type" content="text/html;charset=shift-jis">\n<p>巨<p>\n'  # flake8: noqa


def test_htmltream_http_content_type():
    s = stream_from_fixture('shift-jis-http-content-type').read()
    assert isinstance(s, text_type)
    assert s == '<meta charset="iso-8859-1">\n<p>巨<p>\n'


def test_htmltream_next_encoding():
    stream = stream_from_fixture('shift-jis-next-decoder')
    # HTMLStream likes the look of utf-8 in the <meta> charset
    # but the response is actually encoded in shift-jis so
    # this will raise a UnicodeDecodeError
    with pytest.raises(UnicodeDecodeError):
        stream.read()
    # now try the next encoding (shift-jis)
    stream.next_encoding()
    s = stream.read()
    assert isinstance(s, text_type)
    assert s == '<meta charset="utf-8">\n<p>巨<p>\n'


def test_htmlstream_default_encoding():
    stream = stream_from_fixture('default')
    # first default we try is utf-8
    with pytest.raises(UnicodeDecodeError):
        stream.read()
    # finally we try cp1252 with errors='replace'
    stream.next_encoding()
    s = stream.read()
    assert isinstance(s, text_type)
    assert s == '<p>�®</p>\n'
