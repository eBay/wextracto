""" Helper functions for things that are iterable """

from functools import partial
from itertools import chain
from six import next
from six.moves import map as map_
from .composed import composable


class ZeroValuesError(ValueError):
    """ Zero values were found. """


class MultipleValuesError(ValueError):
    """ More than one value was found. """


@composable
def first(iterable):
    if not hasattr(iterable, '__iter__'):
        # turns out it isn't iterable after all
        return iterable
    i = iter(iterable)
    try:
        v0 = next(i)
    except StopIteration:
        raise ZeroValuesError
    return v0


@composable
def one(iterable):
    if not hasattr(iterable, '__iter__'):
        # turns out it isn't iterable after all
        return iterable
    i = iter(iterable)
    v0 = first(i)
    try:
        next(i)
        raise MultipleValuesError()
    except StopIteration:
        pass
    return v0


@composable
def one_or_none(iterable):
    try:
        return one(iterable)
    except ZeroValuesError:
        return None


@composable
def flatten(iterable):
    subiterables = ((flatten(i) if hasattr(i, '__iter__') else (i,)) for i in iterable)
    return chain.from_iterable(subiterables)


def partial_map(func, *args, **kwargs):
    return composable(partial(map_, func, *args, **kwargs))
