import json

def echo(response):
    if response.headers.getsubtype() == 'json':
        yield json.load(response)
