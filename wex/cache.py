import threading
from functools import wraps


class ComposeCache(dict):

    def __enter__(self):
        thread_local.cache = self

    def __exit__(self, *excinfo):
        try:
            del thread_local.cache
        except AttributeError:
            pass


def cached(f):
    @wraps(f)
    def wrapper(*args):
        cache = getattr(thread_local, 'cache', {})
        key = (f,) + args
        if key in cache:
            return cache[key]
        res = f(*args)
        cache[key] = res
        return res
    return wrapper


thread_local = threading.local()
