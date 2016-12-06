import json
import codecs
import requests.models
from six import BytesIO
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


class Raw(BytesIO):
    version = 11


def get_monkeypatched(monkeypatch, url, **kw):

    request_args = []

    def request(session, *args, **request_kwargs):
        request_args.append((args, request_kwargs))
        response = requests.models.Response()
        response.raw = Raw()
        return response

    monkeypatch.setattr('requests.sessions.Session.request', request)

    for readable in URL(url).get(**kw):
        pass

    return request_args


def test_get_with_timeout(monkeypatch):
    url = 'http://www.example.net'
    timeout = 3.0
    args = get_monkeypatched(monkeypatch, url, timeout=timeout)
    assert len(args) == 1
    assert args[0][0] == ('get', url)
    assert args[0][1].get('timeout') == timeout


def test_get_with_timeout_tuple(monkeypatch):
    url = 'http://www.example.net'
    timeout = (3.0, 4.0)
    args = get_monkeypatched(monkeypatch, url, timeout=timeout)
    assert len(args) == 1
    assert args[0][0] == ('get', url)
    assert args[0][1].get('timeout') == timeout


def test_get_with_timeout_in_url(monkeypatch):
    url = 'http://www.example.net#{"method":{"get":{"timeout":[3,4]}}}'
    timeout = (3, 4)
    args = get_monkeypatched(monkeypatch, url)
    assert len(args) == 1
    assert args[0][0] == ('get', url)
    assert args[0][1].get('timeout') == timeout


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


def test_get_with_params():
    url = 'http://httpbin.org/get'
    # The use case for adding params at '.get' time is for handling
    # authentication tokens to URLs.  The net effect is that the
    # tokens are not saved in the Wex response which is a way of
    # avoiding sharing your access tokens.
    params = {'token': 'secret'}
    for readable in URL(url).get(params=params):
        response = Response.from_readable(readable)
        data = json.load(utf8_reader(response))
        assert data.get('args') == params
        assert response.request_url == url
        assert not 'secret' in response.url



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
