from lxml.html import parse
from wex.iterable import one
from wex.etree import text

def extract(response):
    tree = parse(response)
    yield "name", one(text(tree.xpath('//h1')))
    yield "country", one(text(tree.xpath('//dd[@id="country"]')))
    yield "region", one(text(tree.xpath('//dd[@id="region"]')))
