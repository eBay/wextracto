from lxml.html import parse
from wex.etree import text


def extract(response):
    tree = parse(response)
    return text(tree.xpath('//h1/text()'))
