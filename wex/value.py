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
from __future__ import unicode_literals, print_function
import sys
import json
import logging
from itertools import product
from operator import itemgetter
from bdb import BdbQuit
from six import PY2, binary_type, text_type, reraise
from six.moves import map
from .iterable import walk, flatten, do_not_iter

logger = logging.getLogger(__name__)

TAB = '\t'
NL = '\n'

json_encoder_kwargs = dict(
    separators=(',', ':'),
    default=None,
    sort_keys=True,
    ensure_ascii=False,
)


if PY2:
    json_encoder_kwargs['encoding'] = 'utf-8'


encode_json = json.JSONEncoder(**json_encoder_kwargs).encode


def encode_field(obj):
    try:
        s = encode_json(obj)
        if isinstance(s, binary_type):
            return s.decode('utf-8')
        return s
    except TypeError:
        return '#' + text_type(repr(obj)) + '!'


def should_iter_unless_list(obj):
    # a list is a reasonable value type so don't flatten it
    return (hasattr(obj, '__iter__') and
            not isinstance(obj, do_not_iter + (list,)))


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
        iterables = [map(encode_field, flatten(label))
                     for label in self.labels]
        flattened = flatten(self.value, should_iter_unless_list)
        iterables.append(map(encode_field, flattened))
        for fields in product(*iterables):
            yield TAB.join(fields) + NL

    def label(self, *labels):
        """ Adds zero or more labels to this value. """
        return self.__class__(tuple(labels) + self)


def yield_values(extract, *args, **kw):
    """ Yields ``Value`` objects extracted using ``extract``. """
    exc_info = ()

    try:
        returned = extract(*args, **kw)
        for walker in walk(returned, should_iter_unless_list):
            for value in walker:
                yield Value(value)
    except BdbQuit:
        raise
    except Exception as exc:
        exc_info = sys.exc_info()
        yield Value(exc)

    if any(exc_info) and (Value.exit_on_exc or Value.debug_on_exc):
        if Value.debug_on_exc:
            import traceback
            try:
                import ipdb as pdb
            except ImportError:
                import pdb
                assert pdb
            traceback.print_tb(exc_info[2])
            pdb.post_mortem(exc_info[2])
        else:
            reraise(exc_info[0], exc_info[1], exc_info[2])
