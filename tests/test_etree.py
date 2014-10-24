from __future__ import unicode_literals, print_function
from six import BytesIO
from lxml import html
from operator import itemgetter
from wex.response import Response, parse_headers
from wex import etree as e

example = b"""HTTP/1.1 200 OK
X-wex-url: http://some.com/

<html>
  <head>
    <base href="http://base.com/">
  </head>
  <body>
    <h1>hi</h1>
    <div id="div1">
      <a href="/1"></a>
      <a href="/2"></a>
    </div>
    <div id="iter_text">This is <span>some </span>text.</div>
    <div id="nbsp">&nbsp;</div>
    <ul>
      <li class="num"> 1</li>
      <li class="num"></li>
      <li class="num">2 </li>
    </ul>
  </body>
</html>
"""

example_with_dodgy_url = b"""HTTP/1.1 200 OK
X-wex-url: http://foo.com/bar[]/baz/

<html>
  <body>
      <a href="/1"></a>
  </body>
</html>
"""

item0 = itemgetter(0)


def response(data):
    return Response.from_readable(BytesIO(data))


def test_parse():
    etree = e.parse(response(example))
    assert etree.xpath('//h1/text()') == ['hi']


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
    f = e.xpath('//h1/text()')
    assert f(response(example)) == ['hi']


def test_xpath_re():
    f = e.xpath('//*[re:test(text(), "SOME", "i")]/text()') | list
    assert f(response(example)) == ['some ']


def test_xpath_re_match():
    f = (e.xpath('re:match(//body, "\s+is\s+(some)\s+text", "gi")/text()') |
         list)
    assert f(response(example)) == ['some']


def test_css():
    f = e.css('h1')
    assert [elem.tag for elem in f(response(example))] == ['h1']


def test_attrib():
    f = e.css('#div1 a') | e.attrib('href') | list
    assert f(response(example)) == ['/1', '/2']


def test_attrib_default():
    f = e.css('#div1 a') | e.attrib('nosuch', '') | list
    assert f(response(example)) == ['', '']


def test_attrib_missing_default():
    f = e.css('#div1 a') | e.attrib('nosuch') | list
    assert f(response(example)) == []


def test_href():
    f = e.css('#div1 a') | e.href | list
    assert f(response(example)) == ['http://base.com/1', 'http://base.com/2']


def test_href_single():
    f = e.css('#div1 a') | item0 | e.href
    assert f(response(example)) == 'http://base.com/1'


def test_href_empty():
    f = e.css('#nosuch') | e.href | list
    assert f(response(example)) == []


def test_text_content_object_has_no_method():
    assert e.text_content(object()) == ''


def test_text_content_nbsp():
    func = e.css('#nbsp') | e.text_content | list
    assert func(response(example)) == [u'\xa0']


def test_text_content_html_comment():
    etree = html.fromstring('<html><!-- comment --></html>')
    (comment,) = etree.getchildren()
    assert e.text_content(comment) == ''


def test_list_filter_join_non_list():
    # notice how the empty string gets filtered from the join
    assert e.list_filter_join(['A', '', 'B']) == 'A B'


def test_list_filter_join_non_list():
    non_list = object()
    assert e.list_filter_join(non_list) is non_list


def test_text():
    func = e.css('ul li') | e.text
    assert func(response(example)) == '1 2'


def test_text_list():
    func = e.css('ul li') | e.text_list
    assert func(response(example)) == ['1', '', '2']


def test_base_url_join_not_joinable():
    obj = object()
    def not_joinable(src):
        return obj
    f = e.base_url_join(not_joinable)
    ret = f(e.parse(response(example)))
    assert ret is obj

def test_href_when_url_contains_dodgy_characters():
    f = e.css('a') | e.href | list
    # This will fail if we don't quote/unquote the base_url
    assert f(response(example_with_dodgy_url)) == ['http://foo.com/1']

