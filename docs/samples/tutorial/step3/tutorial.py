from lxml.html import parse
from wex.iterable import one
from wex.etree import text


def extract(response):
    tree = parse(response)
    return one(text(tree.xpath('//h1/text()')))
