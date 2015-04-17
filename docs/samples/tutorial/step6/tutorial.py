from wex.extractor import named
from wex.iterable import one
from wex.etree import xpath, text


extract = named()


@extract.add
def name(response):
    return one(text(xpath('//h1')(response)))


@extract.add
def whoops(response):
    return 1/0


@extract.add
def country(response):
    return one(text(xpath('//dd[@id="country"]')(response)))


@extract.add
def region(response):
    return one(text(xpath('//dd[@id="region"]')(response)))
