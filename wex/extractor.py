""" Loading, combining and using extractor functions """

from __future__ import absolute_import, unicode_literals, print_function
import logging
from functools import wraps
from six.moves.urllib_parse import urlparse
from pkg_resources import iter_entry_points
from .value import yield_values


OMITTED = object()


def chained(*extractors):
    """ Creates an extractor Chains extractors functions to make a new one. """
    return ChainedExtractors(extractors)


class ChainedExtractors(object):

    @property
    def __name__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.extractors)

    def __init__(self, extractors):
        self.extractors = extractors

    def __call__(self, arg0, *args, **kw):
        seek = getattr(arg0, 'seek', None)
        for extractor in self.extractors:
            if seek:
                seek(0)
            values = yield_values(extractor, arg0, *args, **kw)
            for value in values:
                yield value


def labelled(*literals_or_callables):
    """ Wraps an extractor so that the extracted values are labelled. """

    def call(label, arg0):
        return (label(arg0) if hasattr(label, '__call__') else label)

    def labelled_extractor_decorator(extractor):
        @wraps(extractor)
        def labelled_extractor_wrapper(arg0, *args, **kw):

            labels = [call(label, arg0) for label in literals_or_callables]
            if not all(labels):
                # one or more missing labels so don't yield
                return

            for value in yield_values(extractor, arg0, *args, **kw):
                yield value.label(*labels)

        return labelled_extractor_wrapper

    return labelled_extractor_decorator


def attributes(**kw):
    """ Creates a composite extractor from labelled extractors. """
    return Attributes(**kw)

class Attributes(object):

    def __init__(self, **kw):
        self.extractors = {}
        for k, v in kw.items():
            self.add(k, v)

    @property
    def __name__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.extractors.keys())

    def __len__(self):
        return len(self.extractors)

    def __call__(self, *args, **kwargs):
        for name, extractor in self.extractors.items():
            for value in yield_values(extractor, *args, **kwargs):
                yield value.label(name)

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

    def __call__(self, arg0, *args, **kw):
        url = getattr(arg0, 'url', None)
        hostname = urlparse(url).hostname if url else None
        if hostname not in self.extractors:
            self.extractors[hostname] = self.extractor_for_hostname(hostname)
        extractor = self.extractors[hostname]
        return extractor(arg0, *args, **kw)

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
        return chained(*extractors)
