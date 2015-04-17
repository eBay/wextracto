from wex.extractor import named, labelled
from wex.iterable import one
from wex.etree import xpath, text

cheeses = xpath('//h1[@data-icin]')
icin_attr = xpath('@data-icin') | one

attrs = named(name = text,
              country = xpath('following::dd[@id="country"][1]') | text,
              region = xpath('following::dd[@id="region"][1]') | text)

extract_cheese = labelled(icin_attr, attrs)


def extract(response):
    for cheese in cheeses(response):
        for item in extract_cheese(cheese):
            yield item
