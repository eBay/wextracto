import json
from six import BytesIO
from six.moves import map
from wex.form import create_html_parser
from wex.url import URL
from wex.response import Response, parse_headers
from httpproxy import HttpProxy, skipif_travis_ci


def run(**kw):
    url = URL('http://httpbin.org/forms/post')
    custname = 'Giles'
    toppings = ('bacon', 'onion')
    comments = 'Using CSS selector'
    method = {
        'form': {
            'form': [
                ('custname', custname),
                ('topping', toppings),
                ('textarea', comments),
            ]
        }
    }
    url = url.update_fragment_dict(method=method)
    responses = list(map(Response.from_readable, url.get(**kw)))
    # we should have GET and then POST
    assert len(responses) == 2
    data = json.loads(responses[1].read().decode('utf-8'))
    assert (set(data['form'].keys()) ==
            set(['comments', 'custname', 'topping']))
    assert data['form']['custname'] == custname
    assert data['form']['topping'] == list(toppings)
    assert data['form']['comments'] == comments


def test_submit():
    run()


@skipif_travis_ci
def test_submit_using_proxies():
    with HttpProxy() as proxy:
        context = {'proxy': proxy.url}
        run(proxies=proxy.proxies, context=context)
    expected_requests = [
        b'GET http://httpbin.org/forms/post HTTP/1.1',
        b'POST http://httpbin.org/post HTTP/1.1'
    ]
    assert proxy.requests == expected_requests


def create_html_parser_with_content_type(monkeypatch, content_type):
    class HTMLParser(object):
        def __init__(self, **kw):
            self.kw = kw
    monkeypatch.setattr('wex.form.HTMLParser', HTMLParser)
    lines = [content_type, b'', b'']
    CRLF = b'\r\n'
    headers = parse_headers(BytesIO(CRLF.join(lines)))
    return create_html_parser(headers)


def test_create_html_parser(monkeypatch):
    content_type = b'Content-Type:text/html;charset=ISO8859-1'
    parser = create_html_parser_with_content_type(monkeypatch, content_type)
    assert parser.kw == {'encoding': 'windows-1252'}


def test_create_html_parser_charset_lookup_error(monkeypatch):
    content_type = b'Content-Type:text/html;charset=wtf-123'
    parser = create_html_parser_with_content_type(monkeypatch, content_type)
    assert parser.kw == {'encoding': 'wtf-123'}
