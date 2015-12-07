import json
import codecs
from wex.url import URL
from wex.response import Response
from wex.http import decode
from httpproxy import HttpProxy, skipif_travis_ci

utf8_reader = codecs.getreader('UTF-8')


def get(url, **kw):
    codes = []
    for readable in URL(url).get(**kw):
        response = Response.from_readable(readable)
        codes.append(response.code)
        if response.code == 200:
            data = json.load(utf8_reader(decode(response)))
            assert 'headers' in data
    return codes


def test_get():
    url = 'http://httpbin.org/headers'
    assert get(url) == [200]


def test_urllib3_issue_709_gzip():
    # https://github.com/shazow/urllib3/issues/709
    url = 'http://httpbin.org/gzip'
    for response in map(Response.from_readable, URL(url).get()):
        # the partial read should let us see some not-so-magic bytes
        assert response.magic_bytes == b'{\n  "gzi'
        data = json.load(utf8_reader(response))
        assert 'gzipped' in data


def test_urllib3_issue_709_deflate():
    # https://github.com/shazow/urllib3/issues/709
    url = 'http://httpbin.org/deflate'
    for response in map(Response.from_readable, URL(url).get()):
        # the partial read should let us see some not-so-magic bytes
        assert response.magic_bytes == b'{\n  "def'
        data = json.load(utf8_reader(response))
        assert 'deflated' in data


def test_get_with_context():
    url = 'http://httpbin.org/headers'
    for readable in URL(url).get(context={'foo': 'bar'}):
        response = Response.from_readable(readable)
        assert response.headers.get('X-wex-context-foo') == 'bar'


def test_get_with_redirect():
    url = 'http://httpbin.org/redirect-to?url=http://httpbin.org/headers'
    assert get(url) == [302, 200]


def test_get_gzip():
    url = 'http://httpbin.org/gzip'
    for i, readable in enumerate(URL(url).get(decode_content=False)):
        response = Response.from_readable(readable)
        data = json.load(utf8_reader(decode(response)))
        assert data.get('gzipped')
    assert i == 0


def test_post():
    method = {"post": {"data": {"x": "1"}}}
    url = URL('http://httpbin.org/post').update_fragment_dict(method=method)
    for readable in url.get():
        response = Response.from_readable(readable)
        data = json.load(utf8_reader(response))
        assert data['form'] == method['post']['data']


@skipif_travis_ci
def test_get_using_proxies():
    url = 'http://httpbin.org/redirect-to?url=http://httpbin.org/headers'
    with HttpProxy() as proxy:
        proxies = {'http': proxy.url, 'https': proxy.url}
        assert get(url, proxies=proxies) == [302, 200]
    expected = [
        b'GET http://httpbin.org/redirect-to?url=http://httpbin.org/headers HTTP/1.1',
        b'GET http://httpbin.org/headers HTTP/1.1',
    ]
    assert proxy.requests == expected
