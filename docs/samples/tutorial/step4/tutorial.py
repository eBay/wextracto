from lxml.html import parse
from wex.etree import text

def extract(response):
    tree = parse(response)
    yield "name", text(tree.xpath('//h1/text()'))
    yield "country", text(tree.xpath('//dd[@id="country"]'))
    yield "region", text(tree.xpath('//dd[@id="region"]'))
