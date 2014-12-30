from wex.extractor import Attributes
from wex.etree import xpath, text


extract = Attributes()


@extract.attribute
def name(response):
    return text(xpath('//h1')(response))


@extract.attribute
def whoops(response):
    return 1/0


@extract.attribute
def country(response):
    return text(xpath('//dd[@id="country"]')(response))


@extract.attribute
def region(response):
    return text(xpath('//dd[@id="region"]')(response))
