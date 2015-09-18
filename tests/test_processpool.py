import time
import tempfile
import pytest
from multiprocessing import Lock
from wex import processpool
#from test.logging_ import monitor_logging, get_log_records

lock = Lock()


@processpool.do_func
def other_do_func(filename, letter):
    with lock:
        with open(filename, 'a+') as fp:
            fp.write('other={0}\n'.format(letter))
            fp.flush()


@processpool.do_func
def do_func(filename, number):
    with lock:
        with open(filename, 'a+') as fp:
            fp.write('{0}\n'.format(number))
            fp.flush()
    if number == 7:
        work = [
            (other_do_func, [(filename, 'a'), (filename, 'b')]),
        ]
        raise processpool.MoreWork(work)


def test_do_in_pool():
    t = tempfile.NamedTemporaryFile()
    iterable = ((t.name, i) for i in range(3))
    processpool.do(do_func, iterable)
    assert set(t.read().split()) == set([b'0', b'1', b'2'])


def test_do_in_this_process():
    t = tempfile.NamedTemporaryFile()
    processpool.do(do_func, ((t.name, i) for i in range(3)), pool_size=1)
    assert set(t.read().split()) == set([b'0', b'1', b'2'])


def test_more_work_in_this_process():
    t = tempfile.NamedTemporaryFile()
    processpool.do(do_func, ((t.name, i) for i in (7, 8)), pool_size=1)
    assert set(t.read().split()) == set([b'7', b'8', b'other=a', b'other=b'])


def test_more_work_in_pool():
    t = tempfile.NamedTemporaryFile()
    processpool.do(do_func, ((t.name, i) for i in (7, 8)))
    assert set(t.read().split()) == set([b'7', b'8', b'other=a', b'other=b'])


class MyKindOfError(Exception):
    """ Just so we know it's ours. """


def test_error_during_iteration_in_this_process():
    t = tempfile.NamedTemporaryFile()
    def error_during_iteration():
        yield (t.name, 1)
        yield (t.name, 2)
        raise MyKindOfError(t.name)
    iterable = error_during_iteration()
    with pytest.raises(MyKindOfError):
        processpool.do(do_func, iterable, pool_size=1)
    assert set(t.read().split()) == set([b'1', b'2'])


def test_error_during_iteration():
    t = tempfile.NamedTemporaryFile()
    # We have to do a little dance to get an exception
    # that occurs during iteration to not screw up
    # the process pool.
    # If you want to see what I mean try
    def error_during_iteration():
        yield (t.name, 1)
        yield (t.name, 2)
        time.sleep(0.01)
        raise MyKindOfError(t.name)
    iterable = error_during_iteration()
    with pytest.raises(MyKindOfError):
        processpool.do(do_func, iterable)
    assert set(t.read().split()) == set([b'1', b'2'])


def test_do_func_raises_ioerror_exc():
    @processpool.do_func
    def error_do_func(filename, i):
        raise IOError("whoops")
    t = tempfile.NamedTemporaryFile()
    iterable = ((t.name, i) for i in range(3))
    with pytest.raises(IOError):
        processpool.do(error_do_func, iterable, pool_size=1)
    assert set(t.read().split()) == set([])


def test_do_func_raises_keyboard_interrupt():
    @processpool.do_func
    def error_do_func(filename, i):
        raise KeyboardInterrupt("whoops")
    t = tempfile.NamedTemporaryFile()
    iterable = ((t.name, i) for i in range(3))
    with pytest.raises(KeyboardInterrupt):
        processpool.do(error_do_func, iterable, pool_size=1)
    assert set(t.read().split()) == set([])


def test_do_func_raises_system_exit():
    @processpool.do_func
    def error_do_func(filename, i):
        raise SystemExit("whoops")
    t = tempfile.NamedTemporaryFile()
    iterable = ((t.name, i) for i in range(3))
    with pytest.raises(SystemExit):
        processpool.do(error_do_func, iterable, pool_size=1)
    assert set(t.read().split()) == set([])


#@monitor_logging(processpool)
def test_do_func_raises_other_exception():
    # We want to ensure we do not stop extraction on unknown exceptions
    @processpool.do_func
    def error_do_func(filename, i):
        raise MyKindOfError("whoops")
    t = tempfile.NamedTemporaryFile()
    iterable = ((t.name, i) for i in range(3))
    with pytest.raises(MyKindOfError):
        processpool.do(error_do_func, iterable, pool_size=1)
    #logs = [r.getMessage() for r in get_log_records(processpool)]
    #eq_(logs, ['doing work', 'doing work', 'doing work'])


def test_initializer_in_this_process():

    mutable = {}
    def initializer(value):
        mutable['prefix'] = value

    @processpool.do_func
    def do_func_with_initializer(filename, number):
        with open(filename, 'a+') as fp:
            fp.write('{0}:{1}\n'.format(mutable['prefix'], number))
            fp.flush()
    t = tempfile.NamedTemporaryFile()
    processpool.do(do_func_with_initializer,
        ((t.name, i) for i in (7, 8)),
        pool_size=1,
        initializer=initializer,
        initargs=('foo',)
    )
    assert set(t.read().split()) == set([b'foo:7', b'foo:8'])
