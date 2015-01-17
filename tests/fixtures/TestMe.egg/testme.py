import wex.py2compat ; assert wex.py2compat
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


#
# extractors for testing different output generation


def return_list(response):
    return [1, 2]


def return_tuple(response):
    # tuples are used for labelling so we need nested tuples here
    return ((1, 2),)


def return_dict(response):
    # tuples are used for labelling so we need nested tuples here
    return {'a': 1}
