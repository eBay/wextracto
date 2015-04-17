from wex.extractor import named
from wex.etree import xpath, text


extract = named(name = xpath('//h1') | text,
                country = xpath('//dd[@id="country"]') | text,
                region = xpath('//dd[@id="region"]') | text)
