from pkg_resources import working_set, resource_stream, resource_filename
from wex.extractor import (prefixed,
                           chained,
                           Attributes, ExtractorFromEntryPoints)
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

def extractor_with_error(src):
    raise error


def example(src):
    yield ("baz",)


def extract_first_line(response):
    yield (response.readline(),)


def test_prefixed():
    extractor = prefixed(example, lambda x: x, "bar")
    assert list(extractor("foo")) == [("foo", "bar", "baz")]


def test_prefixed_missing():
    def extractor(src):
        yield ("baz",)
    extractor = prefixed(example, lambda x: None, "bar")
    assert list(extractor("foo")) == []


def test_attributes():
    attributes = Attributes()
    attributes.add('foo', lambda v: v)
    actual = list(attributes('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_attributes_keywords():
    attributes = Attributes(foo=lambda v: v)
    actual = list(attributes('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_len():
    attributes = Attributes()
    attributes.add('foo', lambda v: v)
    assert len(attributes) == 1


def test_attribute_add_as_decorator():
    attributes = Attributes()
    @attributes.extractor
    def foo(value):
        return value
    actual = list(attributes('bar'))
    expected = [('foo', 'bar')]
    assert actual, expected
    assert foo('bar') == 'bar'


def test_attribute_generator():
    attributes = Attributes()
    def foo(value):
        for character in value:
            yield character
    attributes.add(foo)
    actual = list(attributes('bar'))
    expected = [('foo', 'b'), ('foo', 'a'), ('foo', 'r'),]
    assert actual == expected
    assert list(foo('bar')) == list('bar')


def test_attribute_exception():
    attributes = Attributes()
    def foo(value):
        raise ValueError(value)
    attributes.add(foo)
    actual = list(attributes('bar'))
    assert len(actual) == 1
    actual_name, actual_value = actual[0]
    assert actual_name == 'foo'
    assert isinstance(actual_value, Exception)


def test_attribute_exception_in_generator():
    attributes = Attributes()
    def foo(value):
        for i, character in enumerate(value):
            if i > 0:
                raise ValueError(character)
            yield character
        raise ValueError(value)
    attributes.add(foo)
    actual = list(attributes('bar'))
    assert len(actual) == 2
    # The first value came out ok...
    assert actual[0] == ('foo', 'b')
    actual_name, actual_value = actual[1]
    assert actual_name == 'foo'
    # But the second one is an error.
    assert isinstance(actual_value, Exception)


def test_extractor_from_entry_points():
    import testme
    extractor = ExtractorFromEntryPoints()
    readable = resource_stream(__name__, 'fixtures/get_this_that')
    for item in Response.items_from_readable(extractor, readable):
        pass
    hostname = 'httpbin.org'
    assert extractor.extractors.keys() == [hostname]
    extractors = set(extractor.extractors[hostname].extractors)
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
    for item in Response.items_from_readable(extractor, readable):
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
    for item in Response.items_from_readable(extractor, readable):
        pass
    hostname = 'www.foo.com'
    assert extractor.extractors.keys() == [hostname]
    extractors = set(extractor.extractors[hostname].extractors)
    assert testme.example_with_hostname_suffix not in extractors
    assert testme.example in extractors


def test_prefixed_error():
    extractor = prefixed(extractor_with_error, lambda x: x, "bar")
    items = list(extractor('foo'))
    assert items == [('foo', 'bar', error,)]


def test_chained_extractor_error():
    extractor = chained([extractor_with_error])
    items = list(extractor('foo'))
    assert items == [(error,)]


def test_chained_extractor_seek():
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    response = Response.from_readable(readable)
    extractor = chained([extract_first_line, extract_first_line])
    items = list(extractor(response))
    assert items == [('# /robots.txt\n',), ('# /robots.txt\n',)]
