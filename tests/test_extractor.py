from pkg_resources import working_set, resource_stream, resource_filename
from wex.extractor import (labelled, chained, attributes, ExtractorFromEntryPoints)
from wex.response import Response




def setup_module():
    entry = resource_filename(__name__, 'fixtures/TestMe.egg')
    working_set.add_entry(entry)


ex1 = """HTTP/1.1 200 OK\r
Content-Type: application/json\r
X-wex-url: http://httpbin.org/headers\r
\r
{
  "headers": {
    "Accept": "*/*",
    "Host": "httpbin.org"
  }
}"""


ex2 = """HTTP/1.1 200 OK\r
Content-Type: application/json\r
X-wex-url: http://doesnotmatch.org/headers\r
\r
{}"""


class MyError(Exception):
    pass

error = MyError()


def extract_arg0(arg0):
    yield (arg0,)


def extract_first_line(response):
    yield (response.readline(),)


def extract_with_error(arg0):
    raise error


def test_chained_error():
    extract = chained(extract_with_error)
    items = list(extract('foo'))
    assert items == [(error,)]


def test_chained_seek():
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    response = Response.from_readable(readable)
    extract = chained(extract_first_line, extract_first_line)
    values = list(extract(response))
    assert values == [(b'# /robots.txt\n',), (b'# /robots.txt\n',)]


def test_labelled():
    labeller  = (lambda x: x)
    extract = labelled(labeller)(extract_arg0)
    assert list(extract("foo")) == [("foo", "foo")]


def test_labelled_missing_label():
    labeller = (lambda x: None)
    @labelled(labeller)
    def extract(src):
        yield ("baz",)
    assert list(extract("foo")) == []


def test_labelled_error():
    labeller = (lambda x: "bar")
    extract = labelled(labeller)(extract_with_error)
    values = list(extract('foo'))
    assert values == [('bar', error,)]


def test_labelled_chain():
    # bug test
    labeller  = (lambda x: x)
    extract = labelled(labeller)(chained(extract_arg0))
    assert list(extract("foo")) == [("foo", "foo")]


def test_attributes():
    attr = attributes()
    attr.add('foo', lambda v: v)
    actual = list(attr('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_attributes_keywords():
    attr = attributes(foo=lambda v: v)
    actual = list(attr('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_len():
    attr = attributes()
    attr.add('foo', lambda v: v)
    assert len(attr) == 1


def test_attribute_add_as_decorator():
    attr = attributes()
    @attr.extractor
    def foo(value):
        return value
    actual = list(attr('bar'))
    expected = [('foo', 'bar')]
    assert actual, expected
    assert foo('bar') == 'bar'


def test_attribute_generator():
    attr = attributes()
    def foo(value):
        for character in value:
            yield character
    attr.add(foo)
    actual = list(attr('bar'))
    expected = [('foo', 'b'), ('foo', 'a'), ('foo', 'r'),]
    assert actual == expected
    assert list(foo('bar')) == list('bar')


def test_attribute_exception():
    attr = attributes()
    def foo(value):
        raise ValueError(value)
    attr.add(foo)
    actual = list(attr('bar'))
    assert len(actual) == 1
    actual_name, actual_value = actual[0]
    assert actual_name == 'foo'
    assert isinstance(actual_value, Exception)


def test_attribute_exception_in_generator():
    attr = attributes()
    def foo(value):
        for i, character in enumerate(value):
            if i > 0:
                raise ValueError(character)
            yield character
        raise ValueError(value)
    attr.add(foo)
    actual = list(attr('bar'))
    assert len(actual) == 2
    # The first value came out ok...
    assert actual[0] == ('foo', 'b')
    actual_name, actual_value = actual[1]
    assert actual_name == 'foo'
    # But the second one is an error.
    assert isinstance(actual_value, Exception)


def test_extractor_from_entry_points():
    import testme
    extract = ExtractorFromEntryPoints()
    readable = resource_stream(__name__, 'fixtures/get_this_that')
    for value in Response.values_from_readable(extract, readable):
        pass
    hostname = 'httpbin.org'
    assert list(extract.extractors.keys()) == [hostname]
    extractors = set(extract.extractors[hostname].extractors)
    expected = set([testme.example, testme.example_with_hostname_suffix])
    assert expected.issubset(extractors)


class FakeLogger(object):

    def __init__(self, name):
        self.name = name
        self.exceptions = []

    def exception(self, *args, **kwargs):
        self.exceptions.append((args, kwargs))

    def getLogger(self, name):
        assert name == self.name
        return self


def extract_with_monkeypatched_logging(monkeypatch, excluded=[]):
    logger = FakeLogger('wex.extractor')
    monkeypatch.setattr('logging.getLogger', logger.getLogger)
    extractor = ExtractorFromEntryPoints(excluded)
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    for value in Response.values_from_readable(extractor, readable):
        pass
    return logger

def test_extractor_from_entry_points_load_error(monkeypatch):
    excluded = []
    logger = extract_with_monkeypatched_logging(monkeypatch, excluded)
    assert len(logger.exceptions) == 1
    assert logger.exceptions[0][0][0].startswith("Failed to load")


def test_extractor_from_entry_points_excluded(monkeypatch):
    excluded = ['nosuch']
    logger = extract_with_monkeypatched_logging(monkeypatch, excluded)
    assert len(logger.exceptions) == 0


def test_extractor_from_entry_points_hostname_suffix_excluded():
    import testme
    extractor = ExtractorFromEntryPoints()
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    for value in Response.values_from_readable(extractor, readable):
        pass
    hostname = 'www.foo.com'
    assert list(extractor.extractors.keys()) == [hostname]
    extractors = set(extractor.extractors[hostname].extractors)
    assert testme.example_with_hostname_suffix not in extractors
    assert testme.example in extractors


