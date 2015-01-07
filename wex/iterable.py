""" Helper functions for things that are iterable """

from types import GeneratorType
from functools import partial
from itertools import islice as islice_
from six import next, string_types
from six.moves import map
from .composed import composable


# We use this a lot, let's help pyflakes spot typos
__iter__ = '__iter__'


class ZeroValuesError(ValueError):
    """ Zero values were found when at least one was expected. """


class MultipleValuesError(ValueError):
    """ More than one value was found when one or none were expected. """


@composable
def first(iterable):
    """ Returns first item from an iterable.

    :param iterable: The iterable.

    If the iterable is empty then ``None`` is returned.
    """
    if not hasattr(iterable, __iter__):
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
    if not hasattr(iterable, __iter__):
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
def flatten(obj, yield_types=string_types):
    """ Yield items from all sub-iterables from obj. """
    stack = [(o for o in [obj])]
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
        else:
            if not hasattr(item, '__iter__') or isinstance(item, yield_types):
                yield item
            else:
                stack.append(iter(item))


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
