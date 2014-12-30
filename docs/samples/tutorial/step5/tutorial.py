from wex.etree import parse, text

def extract(response):
    tree = parse(response)
    yield "name", text(tree.xpath('//h1/text()'))
    yield "whoops", 1/0
    yield "country", text(tree.xpath('//dd[@id="country"]'))
    yield "region", text(tree.xpath('//dd[@id="region"]'))
