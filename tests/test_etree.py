from __future__ import unicode_literals, print_function
from six import BytesIO
from lxml import html
from operator import itemgetter
from wex.cache import Cache
from wex.url import URL
from wex.response import Response, parse_headers
from wex import etree as e
from wex.py2compat import parse_headers
from wex.iterable import flatten

example = b"""HTTP/1.1 200 OK
X-wex-request-url: http://some.com/

<html>
  <head>
    <base href="http://base.com/">
  </head>
  <body>
    <h1>hi</h1>
    <div id="div1">
      <a href="/1"></a>
      <a href=" /2 "></a>
      <a></a>
    </div>
   <img src="http://other.com/src" />
    <div id="links">
      <a href="/1"></a>
      <a href="http://subdomain.base.com/2"></a>
      <a href="http://other.com/"></a>
    </div>
    <div id="iter_text">This is <span>some </span>text.</div>
    <div id="nbsp">&nbsp;</div>
    <div id="br">oh<br>my</div>
    <ul>
      <li class="num"> 1</li>
      <li class="num"></li>
      <li class="num">2 </li>
    </ul>
    <div class="thing">First <span>one thing</span></div>
    <div class="thing">then <span>another thing</span>.</div>
  </body>
</html>
"""

example_with_dodgy_url = b"""HTTP/1.1 200 OK
X-wex-request-url: http://foo.com/bar[]/baz/

<html>
  <body>
      <a href="/1"></a>
  </body>
</html>
"""

item0 = itemgetter(0)


def create_response(data):
    return Response.from_readable(BytesIO(data))


def create_html_parser(monkeypatch, content_type):
    class HTMLParser(object):
        def __init__(self, **kw):
            self.kw = kw
    monkeypatch.setattr(e, 'HTMLParser', HTMLParser)
    lines = [content_type, '', '']
    CRLF = b'\r\n'
    headers = parse_headers(BytesIO(CRLF.join(lines)))
    return e.create_html_parser(headers)


def test_create_html_parser(monkeypatch):
    content_type = 'Content-Type:text/html;charset=ISO8859-1'
    parser = create_html_parser(monkeypatch, content_type)
    assert parser.kw == {'encoding': 'windows-1252'}


def test_create_html_parser_charset_lookup_error(monkeypatch):
    content_type = 'Content-Type:text/html;charset=WTF-123'
    parser = create_html_parser(monkeypatch, content_type)
    assert parser.kw == {'encoding': 'WTF-123'}


def test_parse():
    etree = e.parse(create_response(example))
    assert etree.xpath('//h1/text()') == ['hi']


def test_parse_unreadable():
    obj = object()
    assert e.parse(obj) is obj


def test_parse_ioerror():
    class ProblemResponse(object):
        def __init__(self):
            self.headers = parse_headers(BytesIO())
            self.url = None
        def read(self, *args):
            raise IOError
    response = ProblemResponse()
    etree = e.parse(response)
    assert etree.getroot() is e.UNPARSEABLE


def test_xpath():
    f = e.xpath('//h1/text()') | list
    assert f(create_response(example)) == ['hi']


def test_xpath_re():
    f = e.xpath('//*[re:test(text(), "SOME", "i")]/text()') | list
    assert f(create_response(example)) == ['some ']


def test_xpath_re_match():
    f = (e.xpath('re:match(//body, "\s+is\s+(some)\s+text", "gi")/text()') |
         list)
    assert f(create_response(example)) == ['some']


def test_css():
    f = e.css('h1')
    response = create_response(example)
    res = f(response)
    assert isinstance(res, list)
    assert [elem.tag for elem in res] == ['h1']


def test_css_called_twice():
    f = e.css('h1')
    response = create_response(example)
    with Cache():
        assert f(response)== f(response)


def test_attrib():
    f = e.css('#div1 a') | e.attrib('href') | list
    r = create_response(example)
    assert f(r) == ['/1', ' /2 ', None]


def test_attrib_default():
    f = e.css('#div1 a') | e.attrib('nosuch', '') | list
    assert f(create_response(example)) == ['', '', '']


def test_img_src():
    f = e.css('img') | e.src_url
    res = f(create_response(example))
    assert hasattr(res, '__iter__')
    assert not isinstance(res, list)
    assert list(res) == ['http://other.com/src']


def test_get_base_url():
    response = create_response(example)
    tree = e.parse(response)
    base_url = e.get_base_url(tree)
    assert base_url == 'http://base.com/'


def test_href_url():
    f = e.css('#links a') | e.href_url
    res = f(create_response(example))
    # we want the result to be an iterable, but not a list
    assert hasattr(res, '__iter__')
    assert not isinstance(res, list)
    assert list(res) == ['http://base.com/1']


def test_href_url_same_suffix():
    f = e.css('#links a') | e.href_url_same_suffix
    res = f(create_response(example))
    # we want the result to be an iterable, but not a list
    assert hasattr(res, '__iter__')
    assert not isinstance(res, list)
    assert list(res) == ['http://base.com/1', 'http://subdomain.base.com/2']


def test_href_any_url():
    f = e.css('#links a') | e.href_any_url
    res = f(create_response(example))
    # we want the result to be an iterable, but not a list
    assert hasattr(res, '__iter__')
    assert not isinstance(res, list)
    assert list(res) == ['http://base.com/1',
                         'http://subdomain.base.com/2',
                         'http://other.com/']


def test_href_url_single():
    f = e.css('#div1 a') | item0 | e.href_url
    assert f(create_response(example)) == 'http://base.com/1'


def test_href_empty():
    f = e.css('#nosuch') | e.href_url | list
    assert f(create_response(example)) == []


def test_same_suffix():
    f = e.same_suffix
    base = 'http://example.net'
    assert f((None, None)) == None
    assert f(('', None)) == None
    assert f(('com', None)) == None
    assert f((base, None)) == None
    assert f((base, 'http://example.net')) == 'http://example.net'
    assert f((base, 'http://www.example.net')) == 'http://www.example.net'
    assert f((base, 'javascript:alert("hi")')) == None


def test_same_domain():
    base = 'http://example.net'
    f = e.same_domain
    assert f((None, None)) == None
    assert f(('', None)) == None
    assert f(('com', None)) == None
    assert f((base, None)) == None
    assert f((base, 'http://example.net')) == 'http://example.net'
    assert f((base, 'http://www.example.net')) == None
    assert f((base, 'javascript:alert("hi")')) == None



def test_normalize_space():
    assert e.normalize_space('a') == 'a'


def test_normalize_space_list():
    gen = e.normalize_space(['a'])
    assert list(gen) == ['a']


def test_normalize_space_gen():
    gen = e.normalize_space((ch for ch in 'a'))
    assert list(gen) == ['a']


def test_normalize_space_nested():
    gen = e.normalize_space([['a', ['b', 'c']], ['d']])
    assert list(gen) == ['a b c', 'd']


def test_text():
    f = e.css('h1') | e.text | list
    assert f(create_response(example)) == ['hi']


def test_text_from_xpath():
    f = e.xpath('//h1/text()') | e.text | list
    assert f(create_response(example)) == ['hi']


def test_nbsp():
    func = e.css('#nbsp') | e.itertext | flatten | list
    assert func(create_response(example)) == [u'\xa0']


def test_text_br():
    func = e.css('#br') | e.text | list
    assert func(create_response(example)) == ['oh my']


def test_text_html_comment():
    tree = html.fromstring('<html><!-- comment --></html>')
    assert [t for t in e.text(tree)] == []


def test_join_text():
    func = e.css('ul li') | e.join_text
    assert func(create_response(example)) == '1 2'


def test_list_text():
    func = e.css('ul li') | e.text | list
    assert func(create_response(example)) == ['1', '', '2']


def test_href_when_url_contains_dodgy_characters():
    f = e.css('a') | e.href_url | list
    r = create_response(example_with_dodgy_url)
    # This will fail if we don't quote/unquote the base_url
    assert f(r) == ['http://foo.com/1']


def test_itertext():
    f = e.css('.thing') | e.itertext | flatten | list
    expected = ['First ', 'one thing', 'then ', 'another thing', '.']
    assert f(create_response(example)) == expected


def test_itertext_elem():
    f = e.css('.thing') | (lambda l: l[0]) | e.itertext | list
    expected = ['First ', 'one thing']
    assert f(create_response(example)) == expected
