from __future__ import unicode_literals
from wex.iterable import map_flat
from operator import methodcaller


space_join = ' '.join

def split(*split_args):
    split_func = methodcaller('split', *split_args)
    return map_flat(split_func)

# with default arguments splits whitespace
split_ws = split()

def norm_ws_1(s):
    return space_join(s.split())

norm_ws = map_flat(norm_ws_1)


def partition(separator, **kw):
    norm = kw.pop('norm', norm_ws_1)
    norm_head = kw.pop('norm_head', norm)
    norm_tail = kw.pop('norm_tail', norm)
    def partition_1(s):
        head, sep, tail = s.partition(separator)
        if norm_head:
            head = norm_head(head)
        if norm_tail:
            tail = norm_tail(tail)
        if sep:
            yield (head, tail)
    return map_flat(partition_1)
