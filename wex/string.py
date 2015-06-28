from __future__ import unicode_literals
from wex.iterable import flatten
from operator import methodcaller

strip = methodcaller('strip')

def partition(separator, **kw):
    """ Returns a function that yields tuples created by partitioning
        text using `separator`.
    """
    normalize_head = kw.pop('normalize_head', strip)
    normalize_tail = kw.pop('normalize_tail', strip)
    def _partition(obj):
        for s in flatten(obj):
            head, sep, tail = s.partition(separator)
            if normalize_head:
                head = normalize_head(head)
            if normalize_tail:
                tail = normalize_tail(tail)
            if sep:
                yield (head, tail)
    return _partition
