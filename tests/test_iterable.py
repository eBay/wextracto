import pytest
from wex import iterable as i

def test_one():
    assert i.one((1,)) == 1


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


def test_flatten():
    assert list(i.flatten([['a'], ['b']])) == ['a', 'b']


def test_flatten_string():
    # A string isn't considered iterable so nothing should happen
    assert list(i.flatten('abc')) == ['abc']


def test_flatten_nested():
    assert list(i.flatten([['a'], ['b', 'c']])) == ['a', 'b', 'c']


def test_flatmap():
    f = i.flatmap(str) | list
    assert f(range(2)) == ['0', '1']


def test_islice():
    f = i.islice(1) | list
    assert f(range(2)) == [0]
