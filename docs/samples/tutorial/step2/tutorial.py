from lxml.html import parse

def extract(response):
    tree = parse(response)
    return tree.xpath('//h1/text()')
