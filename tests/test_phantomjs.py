from wex.response import Response
from wex.etree import parse
from wex.url import URL
from six.moves import map
from pkg_resources import resource_filename, working_set


def setup_module():
    entry = resource_filename(__name__, 'fixtures/TestMe.egg')
    working_set.add_entry(entry)


def test_phantomjs():
    url = URL('http://httpbin.org/html')
    method = {"phantomjs":{"evaluate":[["testme","bcr.js"]]}}
    url = url.update_fragment_dict(method=method)
    elements = []
    for response in map(Response.from_readable, url.get()):
        tree = parse(response)
        elements.extend(tree.xpath('//h1'))
    assert len(elements) == 1
    assert 'bcr-left' in elements[0].attrib
    assert 'bcr-top' in elements[0].attrib
    assert 'bcr-right' in elements[0].attrib
    assert 'bcr-bottom' in elements[0].attrib
