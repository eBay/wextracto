""" Helper functions for things that are iterable """

import wex.py2compat ; assert wex.py2compat
from functools import partial, singledispatch
from itertools import islice as islice_
from six import next
from six.moves import map
from .composed import composable


class ZeroValuesError(ValueError):
    """ Zero values were found when at least one was expected. """


class MultipleValuesError(ValueError):
    """ More than one value was found when one or none were expected. """



@singledispatch
def should_iterate(obj):
    return True


@should_iterate.register(str)
def should_iterate_str(obj):
    return False


@should_iterate.register(dict)
def should_iterate_dict(obj):
    return False


@composable
def flatten(obj, should_iterate=should_iterate):
    """ Yield items from all sub-iterables from obj. """
    stack = [iter([obj])]
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
        else:
            # read this as ...
            # if can iterate and should iterate
            if hasattr(item, '__iter__') and should_iterate(item):
                stack.append(iter(item))
            else:
                yield item


def map_when(cond, **kw):
    flatten_func = kw.pop('flatten', flatten)
    filter_func = kw.pop('filter', None)

    def map_when_decorator(func):
        @composable
        #@wraps(func)
        def map_when(arg0):
            if hasattr(arg0, '__iter__') and cond(arg0):
                iterable = flatten_func(arg0) if flatten_func else arg0
                mapped = map(func, iterable)
                if filter_func:
                    return filter_func(mapped)
                return mapped
            return func(arg0)
        return map_when
    return map_when_decorator


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
