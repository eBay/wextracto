from wex.extractor import Attributes
from wex.etree import xpath, text


extract = Attributes(
    name = xpath('//h1') | text,
    country = xpath('//dd[@id="country"]') | text,
    region = xpath('//dd[@id="region"]') | text
)
