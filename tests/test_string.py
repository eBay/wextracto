from wex import string as s


def test_partition():
    f = s.partition(':')
    strings = [' x : 1 ', 'y 1', 'z: 2']
    assert list(f(strings)) == [('x', '1'), ('z', '2')]
