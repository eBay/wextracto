from wex.cache import cached, Cache
import pytest


@cached
def cache_me(x):
    return str(x)


def test_cache():
    with Cache():
        assert cache_me(3) == '3'
        assert cache_me(3) == '3'

def test_cache_unhashable():
    with Cache():
        assert cache_me([3]) == '[3]'
        #assert cache_me([3) == 9



def test_cache_attribute_error():
    with pytest.raises(AttributeError):
        with Cache():
            # create AttributeError in __exit__
            del Cache.local.cache


