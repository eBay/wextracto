""" An extractor is a callable that returns or yields data. For example:

.. code-block:: python

    def extract(response):
        return "something"

The ``response`` parameter here is an instance of
:class:`wex.response.Response`.

Extractors can be combined in various ways.
"""

from __future__ import absolute_import, unicode_literals, print_function
from .value import yield_values


OMITTED = object()


class Chained(object):

    set_trace = None

    def __init__(self, *extractors):
        self.extractors = list(extractors)

    @property
    def __name__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.extractors)


    def chained(self, *args, **kw):

        if self.set_trace:
            # Give a hook for debugging
            self.set_trace()

        # Chained extractors are used in wex.entrypoints.
        # We re-seek the response to position 0 for each
        # extractor in the chain for convenience.
        seek = args and getattr(args[0], 'seek', None)

        for extractor in self.extractors:
            if seek:
                seek(0)
            for value in yield_values(extractor, *args, **kw):
                yield value

    __call__ = chained

    def append(self, extractor):
        self.extractors.append(extractor)
        return extractor

    def insert(self, index, extractor=None):
        def decorator(func):
            self.insert(index, func)
        if extractor is None:
            return decorator
        else:
            return decorator(extractor)


def chained(*extractors):
    """ Returns an extractor that chains the output of other extractors.

    The output is the output from each extractor in sequence.

    :param extractors: an iterable of extractor callables to chain

    For example an extractor function ``extract`` defined as follows:

    .. code-block:: python

        def extract1(response):
            yield "one"

        def extract2(response):
            yield "two"

        extract = chained(extract1, extract2)

    Would produce the following extraction output:

    .. code-block:: shell

        $ wex http://example.net/
        "one"
        "two"

    """
    return Chained(*extractors)



class Named(object):
    """ A extractor that is a collection of named extractors.

    Extractors can be added to the collection on construction
    using keyword arguments for the names or they can be added
    using :meth:`.add`.

    The names are labels in the output produced.  For example, an
    extractor function ``extract`` defined as follows:

    .. code-block:: python

        extract = Named(
            name1 = (lambda response: "one"),
            name2 = (lambda response: "two"),
        )

    Would produce the extraction output something like this:

    .. code-block:: shell

        $ wex http://example.net/
        "name1"    "one"
        "name2"    "two"

    The ordering of sub-extractor output is arbitrary.
    """

    set_trace = None

    def __init__(self, **kw):
        self.extractors = {}
        for k, v in kw.items():
            self.add(v, k)

    @property
    def __name__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.extractors.keys())

    def __len__(self):
        return len(self.extractors)

    def named(self, *args, **kwargs):
        if self.set_trace:
            # Give a hook for debugging
            self.set_trace()
        for name, extractor in self.extractors.items():
            for value in yield_values(extractor, *args, **kwargs):
                yield value.label(name)

    __call__ = named

    def add(self, extractor, label=None):
        """ Add an attribute extractor.

        :param callable extractor: The extractor to be added.
        :param str label: The label for the extractor.
                          This may be ``None`` in which case the
                          extractors ``__name__`` attribute will be used.

        This method returns the extractor added.  This means it can
        also be used as a decorator. For example:

        .. code-block:: python

            attrs = Named()

            @attrs.add
            def attr1(response):
                return "one"
        """
        if label is None:
            label = extractor.__name__
        self.extractors[label] = extractor
        return extractor


def named(**kw):
    """ Returns a :class:`.Named` collection of extractors. """
    return Named(**kw)


class Labelled(object):

    set_trace = None

    def __init__(self, labels, extractor):
        self.labels = labels
        self.extractor = extractor

    def get_labels(self, *args, **kw):
        labels = []
        for label in self.labels:
            if callable(label):
                labels.append(label(*args, **kw))
            else:
                labels.append(label)
        return labels

    def labelled(self, *args, **kw):
        if self.set_trace:
            self.set_trace()
        labels = self.get_labels(*args, **kw)
        if not all(labels):
            # don't yield if any labels are false
            return
        for value in yield_values(self.extractor, *args, **kw):
            yield value.label(*labels)

    __call__ = labelled


def labelled(*args):
    """ Returns an extractor decorator that will label the output an extractor.

    :param literals_or_callables: An iterable of labels or callables.

    Each item in ``literals_or_callables`` may be a literal or a callable.
    Any callable will called with the same parameters as the extractor
    and whatever is returned will by used as a label.

    For example an extractor function ``extract`` defined as follows:

    .. code-block:: python

        def extract1(response):
            yield "one"


        def label2(response):
            return "label2"


        extract = label("label1", label2)(extract1)

    Would produce the following extraction output:

    .. code-block:: shell

        $ wex http://example.net/
        "label1"    "label2"    "one"

    Note that if any of the labels are
    `false <https://docs.python.org/2/library/stdtypes.html#truth-value-testing>`_
    then no output will be generated from that extractor.
    """
    return Labelled(args[:-1], args[-1])


def label(*labels):
    def decorator(extractor):
        return labelled(*(labels + (extractor,)))
    return decorator


class If(object):

    def __init__(self, cond, if_true, if_false):
        self.cond = cond
        self.if_true = if_true
        self.if_false = if_false

    def if_(self, *args, **kw):

        if self.cond(*args, **kw):
            extractor = self.if_true
        else:
            extractor = self.if_false

        if extractor is None:
            return

        for value in yield_values(extractor, *args, **kw):
            yield value

    __call__ = if_


def if_(cond, if_true, if_false=None):
    return If(cond, if_true, if_false)
