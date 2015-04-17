import pytest
from wex import iterable as i


def gen(exc=False):
    yield "<gen>"
    yield gen_1(exc=exc)
    yield "</gen>"

def gen_1(exc):
    yield "<gen_1>"
    if exc:
        raise ValueError("whoops")
    yield gen_1_1()
    yield "</gen_1>"

def gen_1_1():
    yield "<gen_1_1>"
    yield "</gen_1_1>"


gen_walk_chunks= [
    ['<gen>'],
    ['<gen_1>'],
    ['<gen_1_1>', '</gen_1_1>'],
    ['</gen_1>'],
    ['</gen>'],
]


def test_walk():
    chunks = []
    for walkable in i.walk(gen()):
        chunks.append(list(walkable))
    assert chunks == gen_walk_chunks


def test_walk_not_exhausted():
    n = 0
    for walkable in i.walk(gen()):
        n += 1
    assert n == len(gen_walk_chunks)


def test_map_if_iter():
    @i.map_if_iter
    def func(x):
        return x + 1
    assert func(1) == 2
    # this one gets mapped
    assert [y for y in func([1])] == [2]


def test_one():
    assert i.one((1,)) == 1


def test_one_not_iterable():
    assert i.one(1) == 1


def test_one_with_multiple_values():
    with pytest.raises(i.MultipleValuesError):
        i.one((1,2))


def test_one_with_zero_values():
    with pytest.raises(i.ZeroValuesError):
        i.one(())


def test_one_composed():
    f = i.one | str
    assert f((1,)) == '1'


def test_one_or_none():
    i.one_or_none((1,)) == 1


def test_one_or_none_with_no_values():
    i.one_or_none(()) == None


def test_one_or_none_composed():
    f = i.one_or_none | str
    assert f((1,)) == '1'


def test_first():
    f = i.first | str
    assert f((1, 2)) == '1'


def test_first_not_iterable():
    f = i.first | str
    assert f(1) == '1'


def test_flatten():
    assert list(i.flatten([['a'], ['b']])) == ['a', 'b']


def test_flatten_string():
    # A string isn't considered iterable so nothing should happen
    assert list(i.flatten('abc')) == ['abc']


def test_flatten_nested():
    assert list(i.flatten([['a'], ['b', 'c']])) == ['a', 'b', 'c']


def test_islice():
    f = i.islice(1) | list
    assert f(range(2)) == [0]
