""" An extractor is a callable that returns or yields data. For example:

.. code-block:: python

    def extract(response):
        return "something"

The ``response`` parameter here is an instance of 
:class:`wex.response.Response`.

Extractors can be combined in various ways.
"""

from __future__ import absolute_import, unicode_literals, print_function
from functools import wraps
from .value import yield_values


OMITTED = object()


class Chain(object):
    """ A chain of extractors.

    The output is the output from each extractor in sequence.

    :param extractors: an iterable of extractor callables to chain

    For example an extractor function ``extract`` defined as follows:

    .. code-block:: python

        def extract1(response):
            yield "one"

        def extract2(response):
            yield "two"

        extract = Chain(extract1, extract2)

    Would produce the following extraction output:

    .. code-block:: shell

        $ wex http://example.net/
        "one"
        "two"

    """

    @property
    def __name__(self):
        return repr(self)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.extractors)

    def __init__(self, *extractors):
        self.extractors = list(extractors)

    def __call__(self, arg0, *args, **kw):
        seek = getattr(arg0, 'seek', None)
        for extractor in self.extractors:
            if seek:
                seek(0)
            values = yield_values(extractor, arg0, *args, **kw)
            for value in values:
                yield value

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



def label(*label_literals_or_callables):
    """ Returns a decorator that will label the output an extractor.

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

    def call(label, arg0):
        return (label(arg0) if hasattr(label, '__call__') else label)

    def label_decorator(extractor):
        @wraps(extractor)
        def labelled_extractor(arg0, *args, **kw):
            labels = [call(l, arg0) for l in label_literals_or_callables]
            if not all(labels):
                # one or more missing labels so don't yield
                return

            for value in yield_values(extractor, arg0, *args, **kw):
                yield value.label(*labels)

        return labelled_extractor

    return label_decorator


class Attributes(object):
    """ A extractor that is a collection of labelled extractors.

    Extractors can be added to the collection on construction
    using keyword arguments for the labels.  For example, an 
    extractor function ``extract`` defined as follows:

    .. code-block:: python

        extract = Attributes(
            attr1 = (lambda response: "one"),
            attr2 = (lambda response: "two"),
        )

    Would produce the extraction output something like this:

    .. code-block:: shell

        $ wex http://example.net/
        "attr1"    "one"
        "attr2"    "two"

    The ordering of the attributes in the output is arbitrary.
    """

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

    def __call__(self, *args, **kwargs):
        for name, extractor in self.extractors.items():
            for value in yield_values(extractor, *args, **kwargs):
                yield value.label(name)

    def add(self, extractor, label=None):
        """ Add an attribute extractor.

        :param callable extractor: The extractor to be added.
        :param str label: The label for the extractor.
                          This may be ``None`` in which case the
                          extractors ``__name__`` attribute will be used.

        This method returns the extractor added.  This means it can
        also be used as a decorator. For example:

        .. code-block:: python

            attrs = Attributes()

            @attrs.add
            def attr1(response):
                return "one"
        """
        if label is None:
            label = extractor.__name__
        self.extractors[label] = extractor
        return extractor
