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

    def attribute(self, extractor):
        """ Add an extractor using decorator syntax. """
        self.add(extractor)
        return extractor
