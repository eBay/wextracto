import json

def example(src):

    if src.headers.getsubtype() != 'json':
        return

    data = json.load(src)
    for item in data.get('args', {}).items():
        yield item


def example_with_hostname_suffix(src):

    if not src.url or not src.url.endswith('/headers'):
        return

    if src.headers.getsubtype() != 'json':
        return

    data = json.load(src)
    for item in data.get('headers', {}).items():
        yield item
