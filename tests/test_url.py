import os
import pytest
from wex.url import URL, DEFAULT_METHOD, eexist_is_ok
# This is the normal idiom for access to the composable functions
from wex import url as u


def test_fragment_quoted():
    # requests quotes the fragment - but we do know how to unquote
    assert URL('http://foo.com/path#%7B%22a%22%3A1%7D').fragment == {'a': 1}


def test_update_fragment():
    original = 'http://foo.com/path#{"method":"get"}'
    updated = 'http://foo.com/path#{"cheeky":true,"method":"get"}'
    assert URL(original).update_fragment(cheeky=True) == updated


def test_method_no_fragment():
    assert URL('http://foo.com/path').method.name == DEFAULT_METHOD


def test_method_fragment_not_json():
    assert URL('http://foo.com/path#SPID=3').method.name == u.DEFAULT_METHOD


def test_method_fragment_not_json_dict():
    assert URL('http://foo.com/path#{3').method.name == u.DEFAULT_METHOD


def test_method_fragment_no_method_key():
    assert URL('http://foo.com/path#{"foo":1}').method.name == u.DEFAULT_METHOD


def test_method_fragment_method_incorrect_type():
    with pytest.raises(ValueError):
        URL('http://foo.com/path#{"method":1}').method


def test_method_fragment_method_wrong_number_of_keys():
    with pytest.raises(ValueError):
        URL('http://foo.com/path#{"method":{"foo":1,"bar":2}}').method


def test_method_fragment_method_value_is_string():
    url = 'http://foo.com/path#{"method":"foo"}'
    assert URL(url).method.name == "foo"


def test_method_fragment_method_value_is_dict():
    url = 'http://foo.com/path#{"method":{"foo":1}}'
    assert URL(url).method.name == 'foo'


def test_method_without_scheme():
    with pytest.raises(ValueError):
        URL('/foo/bar').method


def test_url_get():
    responses = list(URL('http://httpbin.org/robots.txt').get())
    assert len(responses) == 1
    assert responses[0].readline(2**16) == b'HTTP/1.1 200 OK\r\n'


def test_url_get_missing_recipe():
    with pytest.raises(ValueError):
        URL('http://httpbin.org/robots.txt#{"method":"whoops"}').get()


url1 = 'http://www.foo.com/g?this=1&that=2'
url1_parsed = ('http', 'www.foo.com', '/g', '', 'this=1&that=2', '')


# For each test we use a composed function because that checks
# that we've got the composable decorator on the function.

identity = lambda x: x

parse_url = u.parse_url | identity
public_suffix = u.public_suffix | identity
param = u.url_query_param('this') | identity
param_with_default = u.url_query_param('other', ['2']) | identity
include_query_params = u.filter_url_query('that') | identity
exclude_query_params = u.filter_url_query('this', exclude=True) | identity
strip_url_query = u.strip_url_query | identity


def test_parse_url():
    assert parse_url(url1) == url1_parsed


def test_parse_obj():
    class Response(object):
        url = url1
    assert parse_url(Response()) == url1_parsed


def test_param():
    assert param(url1) == ['1']


def test_param_with_default():
    assert param_with_default(url1) == ['2']


def test_include_query_params():
    assert include_query_params(url1) == 'http://www.foo.com/g?that=2'


def test_exclude_query_params():
    assert exclude_query_params(url1) == 'http://www.foo.com/g?that=2'


def test_strip_url_query():
    assert strip_url_query(url1) == 'http://www.foo.com/g'


def test_public_suffix():
    assert public_suffix(url1) == 'foo.com'


def test_eexist_ok():
    with eexist_is_ok():
        os.mkdir(os.getcwd())

def test_eexist_ok_raises(tmpdir):
    with pytest.raises(OSError):
        # This error isn't supressed because its a different error
        with eexist_is_ok():
            os.unlink(tmpdir.strpath)
