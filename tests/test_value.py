from six import next
from wex.value import Value, yield_values

whoops = ValueError("whoops")



def test_yield_values():
    def ex():
        yield 1
    assert list(yield_values(ex)) == [Value(1)]


def test_labels():
    val = Value(('a', 1))
    assert val.labels == ('a',)


def test_text():
    assert next(Value(('a', 1)).text()) == '"a"\t1\n'


def test_text_error():
    text = next(Value(whoops).text())
    assert text.startswith('#') and text.endswith('!\n')


def test_labels_empty():
    val = Value(1)
    assert val.labels == ()


def test_yield_values_raises_error():
    error = ValueError("whoops")
    def ex():
        raise error
    assert list(yield_values(ex)) == [Value(error)]


def test_yield_values_empty():
    def ex():
        if False:
            yield None
    assert list(yield_values(ex)) == []
