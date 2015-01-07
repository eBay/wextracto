from wex.iterable import one
from wex.etree import parse, text

def extract(response):
    tree = parse(response)
    yield "name", one(text(tree.xpath('//h1/text()')))
    yield "whoops", 1/0
    yield "country", one(text(tree.xpath('//dd[@id="country"]')))
    yield "region", one(text(tree.xpath('//dd[@id="region"]')))
