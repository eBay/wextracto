from pkg_resources import resource_stream, resource_filename, working_set
from wex.response import Response
from wex.entrypoints import extractor_from_entry_points


def setup_module():
    entry = resource_filename(__name__, 'fixtures/TestMe.egg')
    working_set.add_entry(entry)

def test_extractor_from_entry_points():
    import testme
    extract = extractor_from_entry_points()
    readable = resource_stream(__name__, 'fixtures/get_this_that')
    for value in Response.values_from_readable(extract, readable):
        pass
    hostname = 'httpbin.org'
    assert list(extract.extractors.keys()) == [hostname]
    extractors = set(extract.extractors[hostname].extractors)
    expected = set([testme.example, testme.example_with_hostname_suffix])
    assert expected.issubset(extractors)


class FakeLogger(object):

    def __init__(self, name):
        self.name = name
        self.exceptions = []

    def exception(self, *args, **kwargs):
        self.exceptions.append((args, kwargs))

    def getLogger(self, name):
        assert name == self.name
        return self


def extract_with_monkeypatched_logging(monkeypatch, excluded=[]):
    logger = FakeLogger('wex.entrypoints')
    monkeypatch.setattr('logging.getLogger', logger.getLogger)
    extractor = extractor_from_entry_points()
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    for value in Response.values_from_readable(extractor, readable):
        pass
    return logger

def test_extractor_from_entry_points_load_error(monkeypatch):
    excluded = []
    logger = extract_with_monkeypatched_logging(monkeypatch, excluded)
    assert len(logger.exceptions) == 1
    assert logger.exceptions[0][0][0].startswith("Failed to load")


#def test_extractor_from_entry_points_excluded(monkeypatch):
#    excluded = ['nosuch']
#    logger = extract_with_monkeypatched_logging(monkeypatch, excluded)
#    assert len(logger.exceptions) == 0


def test_extractor_from_entry_points_hostname_suffix_excluded():
    import testme
    extractor = extractor_from_entry_points()
    readable = resource_stream(__name__, 'fixtures/robots_txt')
    for value in Response.values_from_readable(extractor, readable):
        pass
    hostname = 'www.foo.com'
    assert list(extractor.extractors.keys()) == [hostname]
    extractors = set(extractor.extractors[hostname].extractors)
    assert testme.example_with_hostname_suffix not in extractors
    assert testme.example in extractors


