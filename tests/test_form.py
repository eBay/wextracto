import json
from six.moves import map
from wex.url import URL
from wex.response import Response
from httpproxy import HttpProxy


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


def test_submit_using_proxies():
    with HttpProxy() as proxy:
        context = {'proxy': proxy.url}
        run(proxies=proxy.proxies, context=context)
    expected_requests = [
        b'GET http://httpbin.org/forms/post HTTP/1.1', 
        b'POST http://httpbin.org/post HTTP/1.1'
    ]
    assert proxy.requests == expected_requests
