from pkg_resources import resource_stream
from wex.response import Response
from wex.sitemaps import urls_from_robots_txt, urls_from_sitemap


def response(resource):
    return Response.from_readable(resource_stream(__name__, resource))


def test_urls_from_robots_txt():
    src = response('fixtures/robots_txt')
    items = list(urls_from_robots_txt(src))
    url = 'http://sitemap.foo.com/SiteMap/sitemap_index.xml.gz#{"robots":true}'
    assert items == [('url', url)]


def test_urls_from_sitemap_index_xml():
    src = response('fixtures/sitemap_index_xml')
    items = list(urls_from_sitemap(src))
    url0 = 'http://sitemap.foo.com/SiteMap/sitemap_0.xml.gz#{"robots":true}'
    url1 = 'http://sitemap.foo.com/SiteMap/sitemap_1.xml.gz#{"robots":true}'
    assert items == [('url', url0), ('url', url1)]


def test_non_sitemap_xml():
    src = response('fixtures/other_xml')
    items = list(urls_from_sitemap(src))
    assert items == []
