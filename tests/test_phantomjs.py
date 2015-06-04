import os
import pytest
from wex.response import Response
from wex.etree import parse
from wex.url import URL
from six.moves import map
from httpproxy import HttpProxy

url = URL('http://httpbin.org/html')
method = {"phantomjs":{"requires":[["wex","js/bcr.js"]]}}
url = url.update_fragment_dict(method=method)

def test_phantomjs():
    elements = []
    context = {'foo': 'bar'}
    for response in map(Response.from_readable, url.get(context=context)):
        tree = parse(response)
        elements.extend(tree.xpath('//h1'))
        assert response.headers.get('X-wex-context-foo') == 'bar'
    assert len(elements) == 1
    assert 'bcr-left' in elements[0].attrib
    assert 'bcr-top' in elements[0].attrib
    assert 'bcr-right' in elements[0].attrib
    assert 'bcr-bottom' in elements[0].attrib


@pytest.mark.skipif('TRAVIS' in os.environ, reason='phantomjs missing setProxy')
def test_phantomjs_using_proxies():
    elements = []
    with HttpProxy() as proxy:
        readables = url.get(proxies=proxy.proxies)
        for response in map(Response.from_readable, readables):
            tree = parse(response)
            elements.extend(tree.xpath('//h1'))
    assert len(elements) == 1
    assert proxy.requests == [b'GET http://httpbin.org/html HTTP/1.1']
