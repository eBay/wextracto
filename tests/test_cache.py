from wex import cache


@cache.cached
def cache_me(x):
    return 3**2


def test_cache():
    with cache.ComposeCache():
        assert cache_me(3) == 9
        assert cache_me(3) == 9


def test_cache_attribute_error():
    with cache.ComposeCache():
        # create AttributeError in __exit__
        del cache.thread_local.cache


