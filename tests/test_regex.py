from wex import regex as r


def test_regroup():
    f = r.group('(\d+)') | list
    assert f('a1 b23') == ['1', '23']


def test_re_groupdict():
    f = r.groupdict('(?P<num>\d+)') | list
    assert f('a1 b23') == [{'num': '1'}, {'num': '23'}]

