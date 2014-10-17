""" Many Wextracto functions are designed for use in composed functions.

Composed functions are functions built from other functions:

.. code-block:: pycon

    >>> from wex.composed import compose
    >>> f = compose(lambda x: x+1, lambda x: x*2)
    >>> f(2)
    6

Functions can be decorated to support composition using the ``|`` operator.

.. code-block:: pycon

    >>> from wex.composed import composable
    >>> @composable
    >>> def add1(x):
    ...     return x+1
    ...
    >>> f = add1 | (lambda x: x*2)
    >>> f(2)
    >>> 6

"""

from itertools import chain


class Composable(object):
    """ Composable objects create :class:`.ComposedFunction` objects.

    For example::

        @Composable.decorate
        def add1(x):
            return x + 1

        def mult2(x):
            return x * 2

        composed = add1 | mult2
    """

    @classmethod
    def decorate(cls, func, **kw):
        """ Decorates a callable. """
        name = getattr(func, '__name__', str(func))
        clsdict = dict(
            __call__=staticmethod(func),
            __doc__=getattr(func, '__doc__', None),
            __name__=getattr(func, '__name__', None),
            __module__=getattr(func, '__module__', None),
        )
        clsdict.update(kw)
        return type(name, (cls,), clsdict)()

    @classmethod
    def __getattr__(cls, name):
        return getattr(cls.__call__, name)

    @classmethod
    def __compose__(cls):
        return (cls.__call__,)

    def __or__(self, rhs):
        return compose(self, rhs)

    def __ror__(self, lhs):
        return compose(lhs, self)

    def __call__(self, arg):
        raise NotImplementedError


def flatten(functions):
    iterable = (getattr(f, 'functions', (f,)) for f in functions)
    return tuple(chain.from_iterable(iterable))


class ComposedFunction(Composable):
    """ ComposedFunction creates a new function by combining functions.

    Here is a small example of building a ComposedFunction::

        def mult2(x):
            return x * 2

        def add1(x):
            return x + 1

        composed = Composed(add1, mult2)

        for x in (1, 2, 3):
            assert composed(x) == mult2(add1(x))

    ComposedFunction objects are :class:`.Composable`.

    The ComposedFunction supports only unary (single argument) functions.
    A ComposedFunction can be built from other ComposedFunction objects.

    For more background information on function composition read this
    `wikipedia article <http://en.wikipedia.org/wiki/Function_composition>`_.
    """

    def __init__(self, *functions):
        self.functions = flatten(functions)

    def __call__(self, arg):
        res = arg
        for func in self.functions:
            res = func(res)
        return res

    def __compose__(self):
        return self.functions

    def __repr__(self):
        return '<%s.%s%r>' % (self.__class__.__module__,
                              self.__class__.__name__,
                              self.functions)


def composable(func):
    """ Short-hand for :meth:`.Composable.decorate`. """
    return Composable.decorate(func)


def compose(*functions):
    """ Create a :class:`.ComposedFunction` from zero more functions. """
    return ComposedFunction(*functions)
