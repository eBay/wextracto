""" Helper functions for things that are iterable """

from types import GeneratorType
from functools import partial
from itertools import islice as islice_
from six import next
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
    try:
        return one(iterable)
    except ZeroValuesError:
        return None

@composable
def gen(obj, yieldable=()):
    """ Return a generator. """
    if isinstance(obj, GeneratorType):
        return obj
    if hasattr(obj, __iter__) and not isinstance(obj, yieldable):
        return (i for i in obj)
    return (i for i in (obj,))


@composable
def flatten(obj, yieldable=()):
    """ Yield sub-objects from obj. """
    stack = [gen(obj)]
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
        else:
            if isinstance(item, yieldable) or not hasattr(item, __iter__):
                yield item
            else:
                stack.append(iter(item))


def flatmap(func, *args, **kwargs):
    """ Return function that maps a function over a flattened iterable. """
    partial_func = partial(func, *args, **kwargs)
    @composable
    def flatmap(iterable):
        return map(partial_func, flatten(iterable))
    return flatmap


def islice(*islice_args):
    @composable
    def islice(iterable):
        return islice_(iterable, *islice_args)
    return islice
