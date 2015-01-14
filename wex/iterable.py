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
def iterate(obj):
    return True


@iterate.register(str)
def iterate_str(obj):
    return False


@iterate.register(dict)
def iterate_dict(obj):
    return False


def maybe_map(func):
    @composable
    #@wraps(func)
    def wrapper(arg0):
        if hasattr(arg0, '__iter__') and iterate(arg0):
            return map(func, arg0)
        return func(arg0)
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


@composable
def flatten(obj, iterate=iterate):
    """ Yield items from all sub-iterables from obj. """
    stack = [iter([obj])]
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
        else:
            if hasattr(item, '__iter__') and iterate(item):
                stack.append(iter(item))
            else:
                yield item


def flatmap(func, *args, **kwargs):
    """ Returns a function that maps a function over a flattened iterable. """
    partial_func = partial(func, *args, **kwargs)
    @composable
    def flatmap(iterable):
        return map(partial_func, flatten(iterable))
    return flatmap


def islice(*islice_args):
    """ Returns a function that will perform ``itertools.islice`` on its input. """
    @composable
    def islice(iterable):
        return islice_(iterable, *islice_args)
    return islice
