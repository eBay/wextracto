from wex import regex as r


def test_regroup():
    f = r.re_group('(\d+)') | list
    assert f('a1 b23') == ['1', '23']


def test_regroup_iterable():
    f = r.re_group('(\d+)') | list
    assert f(['a1 b23']) == ['1', '23']


def test_regroup_nested_iterable():
    f = r.re_group('(\d+)') | list
    assert f([['a1 b23'], 'c3']) == ['1', '23', '3']


def test_re_groupdict():
    f = r.re_groupdict('(?P<num>\d+)') | list
    assert f('a1 b23') == [{'num': '1'}, {'num': '23'}]


def test_re_groupdict_iterable():
    f = r.re_groupdict('(?P<num>\d+)') | list
    assert f(['a1 b23']) == [{'num': '1'}, {'num': '23'}]


def test_re_groupdict_nested_iterable():
    f = r.re_groupdict('(?P<num>\d+)') | list
    assert f([['a1 b23'], 'c3']) == [{'num': '1'}, {'num': '23'}, {'num': '3'}]

