from wex.extractor import attributes, labelled
from wex.url import get_url
from wex.etree import xpath, text


attrs = attributes(
    name = xpath('//h1') | text,
    country = xpath('//dd[@id="country"]') | text,
    region = xpath('//dd[@id="region"]') | text
)

extract = labelled(get_url)(attrs)
