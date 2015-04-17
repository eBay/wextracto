from wex.extractor import label, named
from wex.url import url
from wex.etree import xpath, text


attrs = named(name = xpath('//h1') | text,
              country = xpath('//dd[@id="country"]') | text,
              region = xpath('//dd[@id="region"]') | text)

extract = label(url)(attrs)
