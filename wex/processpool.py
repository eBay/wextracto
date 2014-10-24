"""Wrapper around multiprocessing.Pool to perform extraction"""

import logging
from six.moves import map
from functools import wraps
from contextlib import contextmanager
from multiprocessing import Pool


class MoreWork(Exception):
    """\
    Raised when more work needs to be added to the pool mid-run.

    An example of this would be a response containing a zip. We
    could raise this exception to send processing for files
    within the zip back to the pool for (multi-)processing.

    The 'work' parameter must:
        1. be pickleable
        2. give a sequence of (func, iterable) pairs suitable
           for using to extend the work list.
    """
    def __new__(cls, work):
        instance = Exception.__new__(cls)
        instance.work = work
        return instance


def do_func(f):

    @wraps(f)
    def do_func_wrapper(args):
        """\
        Manages exception propagation in work functions.

        We want to ensure that the parent process sees exceptions
        from child processes.

        For exceptions with specific meanings we just return them.
        For any other exception we also log it so we will see the
        traceback (if logging is configured correctly).
        """

        try:

            if isinstance(args, Exception):
                # yield_exc exception re-routing work-around
                # Coverage never sees this because it only
                # runs in child process, but the tests prove
                # it has happened.
                return args # pragma: no cover

            # Notice how we recieve "args" but call using "*args"
            return f(*args)

        except IOError as exc:
            return exc
        except SystemExit as exc:
            return exc
        except KeyboardInterrupt as exc:
            return exc
        except MoreWork as exc:
            return exc
        except BaseException as exc:
            logging.getLogger(__name__).exception('doing work')
            return exc

    return do_func_wrapper


@contextmanager
def close_and_shutdown(pool):
    try:
        yield pool
    except:
        pool.terminate()
        raise
    else:
        pool.close()
    finally:
        pool.join()


def yield_exc(iterable):
    """\
    part 1 of work-around for processes hanging if we get an exception during
    iteration.
    """
    try:
        for item in iterable:
            yield item
    except Exception as exc:
        yield exc


def do_in_pool(worklist, pool_size, initializer, initargs):
    with close_and_shutdown(Pool(pool_size, initializer, initargs)) as pool:
        while worklist:
            func, iterable = worklist.pop()
            for exc_or_none in pool.imap_unordered(func, yield_exc(iterable)):
                yield exc_or_none


# Special handling for single process "pool".
def do_in_this_process(work, initializer, initargs):
    if initializer is not None:
        initializer(*initargs)
    while work:
        func, iterable = work.pop()
        for exc in map(func, iterable):
            yield exc


def do(func, iterable, pool_size=None, initializer=None, initargs=()):
    """ Send work to the pool. """
    worklist = [(func, iterable)]

    if pool_size != 1:
        results = do_in_pool(worklist, pool_size, initializer, initargs)
    else:
        # This is especially useful for debugging
        results = do_in_this_process(worklist, initializer, initargs)

    for exc_or_none in results:
        if exc_or_none is None:
            # There is no exception - keep calm and carry on
            continue
        if isinstance(exc_or_none, MoreWork):
            worklist.extend(exc_or_none.work)
        else:
            assert isinstance(exc_or_none, BaseException)
            raise exc_or_none
