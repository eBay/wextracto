from wex.extractor import Named
from wex.etree import xpath, text


extract = Named(
    name = xpath('//h1') | text,
    country = xpath('//dd[@id="country"]') | text,
    region = xpath('//dd[@id="region"]') | text
)
