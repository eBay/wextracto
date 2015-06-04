from wex.response import Response
from wex.etree import parse
from wex.url import URL
from six.moves import map


def test_phantomjs():
    url = URL('http://httpbin.org/html')
    method = {"phantomjs":{"requires":[["wex","js/bcr.js"]]}}
    url = url.update_fragment_dict(method=method)
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
