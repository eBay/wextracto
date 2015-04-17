from pkg_resources import working_set, resource_stream, resource_filename
from wex.extractor import label, labelled, chained, named
from wex.response import Response


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


my_error = MyError()


def setup_module():
    # This egg has [wex] entry points we use for testing
    entry = resource_filename(__name__, 'fixtures/TestMe.egg')
    working_set.add_entry(entry)


def extract_arg0(arg0):
    yield (arg0,)


def extract_first_line(response):
    yield (response.readline(),)


def extract_with_error(arg0):
    raise my_error


def test_chained_extractor_raises():
    extract = chained(extract_with_error)
    items = list(extract('foo'))
    assert items == [(my_error,)]


def test_chained_does_seek_response():
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    response = Response.from_readable(readable)
    # use the same extractor twice
    extract = chained(extract_first_line, extract_first_line)
    values = list(extract(response))
    # and we get the same first line because chained re-seeks to 0
    assert values == [(b'# /robots.txt\n',), (b'# /robots.txt\n',)]


def test_label():
    labeller  = (lambda x: x)
    extract = label(labeller)(extract_arg0)
    assert list(extract("foo")) == [("foo", "foo")]


def test_label_missing_label():
    labeller = (lambda x: None)
    @label(labeller)
    def extract(src):
        yield ("baz",)
    assert list(extract("foo")) == []


def test_labelled_error():
    labeller = (lambda x: "bar")
    extract = labelled(labeller, extract_with_error)
    values = list(extract('foo'))
    assert values == [('bar', my_error,)]


def test_labelled_chained():
    # bug test
    labeller  = (lambda x: x)
    extract = labelled(labeller, chained(extract_arg0))
    assert list(extract("foo")) == [("foo", "foo")]


def test_label_named():
    # bug test
    labeller  = (lambda x: x)
    n = named(a1=(lambda x: 'bar'))
    extract = label(labeller)(n)
    assert list(extract("foo")) == [("foo", "a1", "bar")]


def test_named():
    n= named()
    n.add(lambda v: v, 'foo')
    actual = list(n('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_nameds_keywords():
    n = named(foo=lambda v: v)
    actual = list(n('bar'))
    expected = [('foo', 'bar')]
    assert actual == expected


def test_named_len():
    n = named()
    n.add('foo', lambda v: v)
    assert len(n) == 1


def test_named_add_as_decorator():
    n = named()
    @n.add
    def foo(value):
        return value
    actual = list(n('bar'))
    expected = [('foo', 'bar')]
    assert actual, expected
    assert foo('bar') == 'bar'


def test_named_extractor_is_generator():
    n = named()
    def foo(value):
        for character in value:
            yield character
    n.add(foo)
    actual = list(n('bar'))
    expected = [('foo', 'b'), ('foo', 'a'), ('foo', 'r'),]
    assert actual == expected
    assert list(foo('bar')) == list('bar')


def test_named_extractor_raises():
    n = named()
    def foo(value):
        raise ValueError(value)
    n.add(foo)
    actual = list(n('bar'))
    assert len(actual) == 1
    actual_name, actual_value = actual[0]
    assert actual_name == 'foo'
    assert isinstance(actual_value, Exception)


def test_named_exception_in_generator():
    n = named()
    def foo(value):
        for i, character in enumerate(value):
            if i > 0:
                raise ValueError(character)
            yield character
        raise ValueError(value)
    n.add(foo)
    actual = list(n('bar'))
    assert len(actual) == 2
    # The first value came out ok...
    assert actual[0] == ('foo', 'b')
    actual_name, actual_value = actual[1]
    assert actual_name == 'foo'
    # But the second one is an error.
    assert isinstance(actual_value, Exception)
