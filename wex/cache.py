import threading
from .composed import wraps


class Cache(dict):

    local = threading.local()

    def __enter__(self):
        try:
            stack = self.local.stack
        except AttributeError:
            stack = self.local.stack = []
        stack.append(self)
        return self

    def __exit__(self, *exc_info):
        popped = self.local.stack.pop()
        assert popped is self

    @classmethod
    def get(cls):
        try:
            stack = cls.local.stack
        except AttributeError:
            pass
        else:
            if stack:
                return stack[-1]
        return {}


def cached(f):
    """ Decorator to cache results keyed by function arguments. """

    @wraps(f)
    def wrapper(*args):
        cache = Cache.get()
        key = (f,) + args
        try:
            return cache[key]
        except TypeError:
            return f(*args)
        except KeyError:
            result = cache[key] = f(*args)
            return result

    return wrapper
