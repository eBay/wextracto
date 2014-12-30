import threading
from functools import wraps


class Cache(dict):

    local = threading.local()

    def __enter__(self):
        self.local.cache = self

    def __exit__(self, *exc_info):
        del self.local.cache

    @classmethod
    def get(cls):
        return getattr(cls.local, 'cache', {})


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
