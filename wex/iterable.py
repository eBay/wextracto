""" Helper functions for things that are iterable """

import wex.py2compat ; assert wex.py2compat
from itertools import chain, islice as islice_
from six import next, string_types
from six.moves import map, filter
from .composed import composable, wraps


class ZeroValuesError(ValueError):
    """ Zero values were found when at least one was expected. """


class MultipleValuesError(ValueError):
    """ More than one value was found when one or none were expected. """


# these are the types we do not want to iterate.
do_not_iter = tuple(string_types) + (dict, tuple)


def _do_not_iter_append(typeobj):
    # do_not_iter needs to be a tuple because we pass it to isinstance
    # but we want to append things so this makes it a little bit mutable
    global do_not_iter
    do_not_iter = do_not_iter + (typeobj,)


def should_iter(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, do_not_iter)


def should_iter_list(obj):
    return hasattr(obj, '__iter__') and not isinstance(obj, do_not_iter + (list,))


def walk(obj, should_iter=should_iter):

    def _walk(iterator):
        # pro-tip: step *into* this next line to debug generators
        for obj in iterator:
            if should_iter(obj):
                stack.append(iter(obj))
                return
            yield obj
        # iterator is now exhausted
        stack.pop()

    if not should_iter(obj):
        yield iter([obj])
        return

    # our stack of iterators - this is how we walk
    stack = [iter(obj)]

    # keep yielding generators until the stack is empty
    while stack:
        gen = _walk(stack[-1])
        yield gen
        # we expect that the generator will have been
        # exhausted by the time we get here, but we make
        # sure it is because otherwise the walk won't stop!
        for _ in gen:
            pass


@composable
def flatten(obj, should_iter=should_iter):
    """ Yield objects from all sub-iterables from obj. """
    return chain.from_iterable(walk(obj, should_iter))


@composable
def flatten_list(obj, should_iter=should_iter):
    """ Yield objects from all sub-iterables from obj. """
    return chain.from_iterable(walk(obj, should_iter_list))


def map_if_iter(func, should_iter=should_iter):
    @composable
    @wraps(func)
    def _map_if_iter(arg):
        if should_iter(arg):
            return map(func, arg)
        else:
            return func(arg)
    return _map_if_iter



def filter_if_iter(func):
    @composable
    @wraps(func)
    def wrapper(arg):
        if not should_iter(arg):
            return arg
        else:
            return filter(func, arg)
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


def islice(*islice_args):
    """ Returns a function that will perform ``itertools.islice`` on its input. """
    @composable
    def islice(iterable):
        return islice_(iterable, *islice_args)
    return islice
