""" Extracted data values are represented with tab-separated fields.
The right-most field on each line is the value, all preceding fields
are labels that describe the value.
The labels and the value are all JSON encoded.

So for example, a value 9.99 with a labels ``product`` and ``price`` would 
look like::

    "product"\t"price"\t9.99\n

And we could decode this line with the following Python snippet:

.. code-block:: pycon

    >>> import json
    >>> line = '"product"\\t"price"\\t9.99\\n'
    >>> [json.loads(s) for s in line.split('\\t')]
    [u'product', u'price', 9.99]

Using tab-delimiters is convenient for downstream processing using Unix 
command line tools such as :command:`cut` and :command:`grep`.
"""

import sys
from json import JSONEncoder
from itertools import product
from functools import partial
from operator import itemgetter
from six import PY2, text_type, reraise
from six.moves import map
import logging; logger = logging.getLogger(__name__)
from .iterable import flatten, do_not_iter


TAB = '\t'
NL = '\n'

if PY2:
    JSONEncoder = partial(JSONEncoder, encoding='UTF-8')

json_encode = JSONEncoder(
    skipkeys=False,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=(',', ':'),
    default=None,
    sort_keys=True,
    # may need to make this an argument at some point,
    # but for now let's assume UTF-8 is ok on the output.
    ensure_ascii=False,
).encode


def encode(obj):
    try:
        return json_encode(obj)
    except TypeError:
        return '#' + text_type(repr(obj)) + '!'


class Value(tuple):

    exit_on_exc = False
    debug_on_exc = False

    value = property(itemgetter(-1))
    labels = property(itemgetter(slice(0, -1)))

    def __new__(cls, value=(None,)):
        if not isinstance(value, tuple):
            value = (value,)
        return super(Value, cls).__new__(cls, value)

    def text(self):
        """ Returns the text this value as a labelled JSON line. """
        iterables = [map(encode, flatten(label)) for label in self.labels]
        iterables.append(map(encode, flatten_non_json(self.value)))
        for fields in product(*iterables):
            yield TAB.join(fields) + NL

    def label(self, *labels):
        """ Adds zero or more labels to this value. """
        return self.__class__(tuple(labels) + self)


# we don't want to flatten anything that is JSON encodable
flatten_non_json = partial(flatten,
                           unless_isinstance=do_not_iter + (list, tuple, dict))

def yield_values(extract, *args, **kw):
    """ Yields ``Value`` objects extracted using ``extract``. """
    exc_info = ()

    try:
        results = extract(*args, **kw)
        for value in flatten_non_json(results):
            yield Value(value)
    except Exception as exc:
        exc_info = sys.exc_info()
        yield Value(exc)

    if any(exc_info) and (Value.exit_on_exc or Value.debug_on_exc):
        if Value.debug_on_exc:
            import pdb
            pdb.post_mortem(exc_info[2])
        else:
            reraise(exc_info[0], exc_info[1], exc_info[2])
