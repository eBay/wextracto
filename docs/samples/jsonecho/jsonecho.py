import json

def echo(response):
    if not response.headers.getsubtype() == 'json':
        return
    yield (json.load(response),)
