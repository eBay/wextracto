import json
import codecs
from wex.url import URL
from wex.response import Response
from wex.http import decode

utf8_reader = codecs.getreader('UTF-8')

def test_get():
    url = 'http://httpbin.org/headers'
    assert get(url) == [200]


def test_get_with_redirect():
    url = 'http://httpbin.org/redirect-to?url=http://httpbin.org/headers'
    assert get(url) == [302, 200]


def get(url):
    codes = []
    for readable in URL(url).get():
        response = Response.from_readable(readable)
        codes.append(response.code)
        if response.code == 200:
            data = json.load(utf8_reader(decode(response)))
            assert 'headers' in data
    return codes


def test_get_gzip():
    url = 'http://httpbin.org/gzip'
    for i, readable in enumerate(URL(url).get(decode_content=False)):
        response = Response.from_readable(readable)
        assert response.headers.get('X-wex-has-gzip-magic') == '1'
        data = json.load(utf8_reader(decode(response)))
        assert data.get('gzipped')
    assert i == 0


def test_post():
    method = {"post":{"data":{"x":"1"}}}
    url = URL('http://httpbin.org/post').update_fragment(method=method)
    for readable in url.get():
        response = Response.from_readable(readable)
        data = json.load(utf8_reader(response))
        assert data['form'] == method['post']['data']
