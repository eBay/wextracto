import json
import codecs


def example(src):

    if src.headers.get_content_subtype() != 'json':
        return

    data = json.load(codecs.getreader('UTF-8')(src))
    for item in data.get('args', {}).items():
        yield item


def example_with_hostname_suffix(src):

    if not src.url or not src.url.endswith('/headers'):
        return

    if src.headers.get_content_subtype() != 'json':
        return

    data = json.load(codecs.getreader('UTF-8')(src))
    for item in data.get('headers', {}).items():
        yield item
