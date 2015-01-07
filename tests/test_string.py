from wex import string as s


def test_split_ws():
    gen = (str for str in (' a ', ' b '))
    assert list(s.split_ws(gen)) == [['a'], ['b']]
