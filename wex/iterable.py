""" Helper functions for things that are iterable """

import wex.py2compat ; assert wex.py2compat
from functools import partial
from itertools import islice as islice_
from lxml.etree import _Element
from six import next, string_types
from six.moves import map, filter
from .composed import composable


class ZeroValuesError(ValueError):
    """ Zero values were found when at least one was expected. """


class MultipleValuesError(ValueError):
    """ More than one value was found when one or none were expected. """


# we never want to iterate (or flatten) things of these types
do_not_iter = string_types + (_Element,)


@composable
def flatten(item, unless_isinstance=do_not_iter):
    """ Yield items from all sub-iterables from obj. """
    stack = []
    while True:

        if not hasattr(item, '__iter__') or isinstance(item, unless_isinstance):
            yield item
        else:
            stack.append(iter(item))

        while stack:
            try:
                item = next(stack[-1])
                break
            except StopIteration:
                stack.pop()

        if not stack:
            break


def map_if_iter(func):
    @composable
    #@wraps(func)
    def wrapper(arg0):
        if not hasattr(arg0, '__iter__') or isinstance(arg0, do_not_iter):
            return func(arg0)
        else:
            return map(func, flatten(arg0))
    return wrapper


def filter_if_iter(func):
    @composable
    def wrapper(arg0):
        if not hasattr(arg0, '__iter__') or isinstance(arg0, do_not_iter):
            return arg0
        else:
            return filter(func, arg0)
    return wrapper



@composable
def first(iterable):
    """ Returns first item from an iterable.

    :param iterable: The iterable.

    If the iterable is empty then ``None`` is returned.
    """
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
    """ Returns an item from an iterable of exactly one element.

    If the iterable comprises zero elements then :exc:`.ZeroValuesError` is
    raised.
    If the iterable has more than one element then :exc:`.MultipleValuesError` is
    raised.
    """
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
    """ Returns one item or ``None`` from an iterable of length one or zero.

    If the iterable is empty then ``None`` is returned.

    If the iterable has more than one element then :exc:`.MultipleValuesError` is
    raised.
    """
    try:
        return one(iterable)
    except ZeroValuesError:
        return None


def map_partial(func, *args, **kwargs):
    """ Returns a function that maps a function over a flattened iterable. """
    partial_func = partial(func, *args, **kwargs)
    @composable
    def map_partial(iterable):
        return map(partial_func, iterable)
    return map_partial


def map_flat(func, *args, **kwargs):
    return flatten | map_partial(func, *args, **kwargs)


def islice(*islice_args):
    """ Returns a function that will perform ``itertools.islice`` on its input. """
    @composable
    def islice(iterable):
        return islice_(iterable, *islice_args)
    return islice
