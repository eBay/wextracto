from wex.cache import cached, Cache
import pytest


@cached
def cache_me(x):
    return str(x)


def test_cache():
    with Cache() as c1:
        assert cache_me(3) == '3'
        assert cache_me(3) == '3'
        assert Cache.get() is c1
        assert len(Cache.get()) == 1


def test_cache_unhashable():
    with Cache():
        assert cache_me([3]) == '[3]'
        assert len(Cache.get()) == 0


def test_nested_caches():
    with Cache() as c1:
        with Cache() as c2:
            assert Cache.get() is c2
            assert len(Cache.local.stack) == 2
        assert Cache.get() is c1
        assert len(Cache.local.stack) == 1
    assert len(Cache.local.stack) == 0


def test_cache_attribute_error():
    with pytest.raises(AttributeError):
        with Cache():
            # create AttributeError in __exit__
            del Cache.local.stack
