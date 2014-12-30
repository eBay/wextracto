from pkg_resources import working_set, resource_stream, resource_filename
from wex.extractor import labelled, chained, Attributes
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


def test_labelled_attributes():
    # bug test
    labeller  = (lambda x: x)
    attr = Attributes(a1=(lambda x: 'bar'))
    extract = labelled(labeller)(attr)
    assert list(extract("foo")) == [("foo", "a1", "bar")]


def test_attributes():
    attr = Attributes()
    attr.add(lambda v: v, 'foo')
    actual = list(attr('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_attributes_keywords():
    attr = Attributes(foo=lambda v: v)
    actual = list(attr('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_len():
    attr = Attributes()
    attr.add('foo', lambda v: v)
    assert len(attr) == 1


def test_attribute_add_as_decorator():
    attr = Attributes()
    @attr.add
    def foo(value):
        return value
    actual = list(attr('bar'))
    expected = [('foo', 'bar')]
    assert actual, expected
    assert foo('bar') == 'bar'


def test_attribute_generator():
    attr = Attributes()
    def foo(value):
        for character in value:
            yield character
    attr.add(foo)
    actual = list(attr('bar'))
    expected = [('foo', 'b'), ('foo', 'a'), ('foo', 'r'),]
    assert actual == expected
    assert list(foo('bar')) == list('bar')


def test_attribute_exception():
    attr = Attributes()
    def foo(value):
        raise ValueError(value)
    attr.add(foo)
    actual = list(attr('bar'))
    assert len(actual) == 1
    actual_name, actual_value = actual[0]
    assert actual_name == 'foo'
    assert isinstance(actual_value, Exception)


def test_attribute_exception_in_generator():
    attr = Attributes()
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
