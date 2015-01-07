from wex.extractor import Attributes, label
from wex.iterable import one
from wex.etree import xpath, text

cheeses = xpath('//h1[@data-icin]')

icin_attr = xpath('@data-icin') | one

attrs = Attributes(
    name = text,
    country = xpath('following::dd[@id="country"][1]') | text,
    region = xpath('following::dd[@id="region"][1]') | text
)

extract_cheese = label(icin_attr)(attrs)


def extract(response):
    for cheese in cheeses(response):
        for item in extract_cheese(cheese):
            yield item
