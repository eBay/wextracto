from wex.extractor import label, Attributes
from wex.url import get_url
from wex.etree import xpath, text


attrs = Attributes(
    name = xpath('//h1') | text,
    country = xpath('//dd[@id="country"]') | text,
    region = xpath('//dd[@id="region"]') | text
)

extract = label(get_url)(attrs)
