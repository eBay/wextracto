import json
from six.moves import map
from wex.url import URL
from wex.response import Response

def test_submit():
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
    responses = list(map(Response.from_readable, url.get()))
    # we should have GET and then POST
    assert len(responses) == 2
    data = json.load(responses[1])
    assert (set(data['form'].keys()) ==
            set(['comments', 'custname', 'topping']))
    assert data['form']['custname'] == custname
    assert data['form']['topping'] == list(toppings)
    assert data['form']['comments'] == comments
