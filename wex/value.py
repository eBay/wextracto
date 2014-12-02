#from .output import json_encode
import sys
from types import GeneratorType
from json import JSONEncoder
from functools import partial
from operator import itemgetter
from itertools import chain
from six import PY2, text_type
from six.moves import map
import logging; logger = logging.getLogger(__name__)


exit_on_first_exception = False


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



class Value(tuple):

    value = property(itemgetter(-1))
    labels = property(itemgetter(slice(0, -1)))

    def __new__(cls, value=(None,)):
        if not isinstance(value, tuple):
            value = (value,)
        return super(Value, cls).__new__(cls, value)

    def text(self):
        """ Returns the text this value as a labelled JSON line. """
        try:
            encoded = json_encode(self.value)
        except:
            encoded = '#' + text_type(repr(self.value)) + '!'
        return TAB.join(chain(map(text_type, self.labels), (encoded,))) + NL

    def label(self, *labels):
        """ Adds zero or more labels to this value. """
        return self.__class__(tuple(map(text_type, labels)) + self)


def yield_values(extract, *args, **kw):
    """ Yields ``Value`` objects extracted using ``extract``. """
    exc_info = ()

    try:
        res = extract(*args, **kw)
        if type(res) is GeneratorType:
            for val in res:
                yield Value(val)
        else:
            yield Value(res)
    except Exception as exc:
        exc_info = sys.exc_info()
        yield Value(exc)

    if any(exc_info) and exit_on_first_exception:
        raise exc_info
