""" Loading, combining and using extractor functions """

from __future__ import absolute_import, unicode_literals, print_function
import logging
from six.moves.urllib_parse import urlparse
from pkg_resources import iter_entry_points


OMITTED = object()


class ChainedExtractor(object):
    """ An extractor made from chaining extractors """

    def __init__(self, extractors):
        self.extractors = extractors

    def __call__(self, src, **kw):
        for extractor in self.extractors:
            try:
                if hasattr(src, 'seek'):
                    src.seek(0)
                for item in extractor(src):
                    yield item
            except Exception as exc:
                yield (exc,)


def chained(extractors):
    return ChainedExtractor(extractors)


def prefixed(extractor, *prefixes):

    def _prefixed(src, **kw):
        prefix = tuple(p(src) if hasattr(p, '__call__') else p for p in prefixes)
        if not all(prefix):
            return
        try:
            for item in extractor(src, **kw):
                yield prefix + item
        except Exception as exc:
            yield prefix + (exc,)

    return _prefixed


class Attributes(object):
    """Extractor assigning prefix names to sub-extractors."""

    def __init__(self, **kw):
        self.extractors = {}
        for k, v in kw.items():
            self.add(k, v)

    def __len__(self):
        return len(self.extractors)

    def __call__(self, *args, **kw):
        for name, extractor in self.extractors.items():

            try:
                val = extractor(*args, **kw)
            except Exception as exc:
                logging.getLogger(__name__).exception("WHOOPS %r %r", name, extractor)
                yield name, exc
                continue

            if not hasattr(val, '__iter__') or isinstance(val, (list, tuple)):
                yield name, val
            else:
                try:
                    for value in val:
                        yield name, value
                except Exception as exc:
                    yield name, exc

    def add(self, extractor_or_name, extractor=OMITTED):
        """ Add attribute function decorator/add method. """
        if extractor is OMITTED:
            name = extractor_or_name.__name__
            extractor = extractor_or_name
        else:
            name = extractor_or_name
        self.extractors[name] = extractor

    def extractor(self, extractor):
        """ Add an extractor using decorator syntax. """
        self.add(extractor)
        return extractor


class ExtractorFromEntryPoints(object):
    """ An extractor that loads sub-extractors from entry points. 

    Sub-extractors may be hostname specific.  This is indicated by
    using a leading '.' in the entry point name.
    """

    def __init__(self, excluded=[]):
        self.extractors = {}
        self.excluded = excluded

    def __call__(self, src):
        hostname = urlparse(src.url).hostname if src.url else None
        if hostname not in self.extractors:
            self.extractors[hostname] = self.extractor_for_hostname(hostname)
        extractor = self.extractors[hostname]
        return extractor(src)

    def extractor_for_hostname(self, hostname):
        extractors = []
        entry_point_group = 'wex'
        for entry_point in iter_entry_points(entry_point_group):
            if entry_point.name in self.excluded:
                continue
            if hostname and entry_point.name.startswith('.'):
                dotname = '.' + hostname
                if not dotname.endswith(entry_point.name):
                    continue
            try:
                extractor = entry_point.load()
            except Exception:
                logger = logging.getLogger(__name__)
                logger.exception("Failed to load [%s] entry point '%s'",
                                 entry_point_group, entry_point.name)
                continue
            extractors.append(extractor)
        return chained(extractors)
