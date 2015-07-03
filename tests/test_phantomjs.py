from subprocess import check_output, CalledProcessError
from six.moves import map
import pytest
from wex.response import Response
from wex.etree import parse
from wex.url import URL
from httpproxy import HttpProxy, skipif_travis_ci

url = URL('http://httpbin.org/html')
method = {"phantomjs":{"requires":[["wex","js/bcr.js"]]}}
url = url.update_fragment_dict(method=method)

try:
    version = check_output(['phantomjs', '--version'])
except CalledProcessError:
    version_info = (0, 0, 0)
else:
    version_info = tuple(map(int, version.split(b'.')))

old_phantomjs_version = pytest.mark.skipif(version_info < (2, 0, 0),
                                           reason='phantomjs version to old')


@old_phantomjs_version
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


@skipif_travis_ci
@old_phantomjs_version
def test_phantomjs_using_proxies():
    elements = []
    with HttpProxy() as proxy:
        readables = url.get(proxies=proxy.proxies)
        for response in map(Response.from_readable, readables):
            tree = parse(response)
            elements.extend(tree.xpath('//h1'))
    assert len(elements) == 1
    assert proxy.requests == [b'GET http://httpbin.org/html HTTP/1.1']
