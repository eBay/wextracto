import pickle
import pytest
from pkg_resources import resource_filename
from six import BytesIO, next
from wex.response import DEFAULT_READ_SIZE
from wex.readable import (ChainedReadable,
                          TeeReadable,
                          Open,
                          partial as partial_,
                          tarfile_open,
                          readables_from_paths,
                          readables_from_file_path)


def read_chunks(readable, size=DEFAULT_READ_SIZE):
    chunks = []
    while True:
        chunk = readable.read(size)
        if not chunk:
            break
        chunks.append(chunk)
    return b''.join(chunks)


def test_readables_from_paths_url():
    data = []
    for readable in readables_from_paths(['http://httpbin.org/headers']):
        data.append(read_chunks(readable))
    assert data[0].startswith('HTTP/1.1 200 OK')


def test_readables_from_paths_dir(tmpdir):
    dir1 = tmpdir.mkdir('dir1')
    wexin = dir1.join('0.wexin')
    with wexin.open('w') as fp:
        fp.write('foo')
    data = []
    for readable in readables_from_paths([tmpdir.strpath]):
        data.append(read_chunks(readable))
    assert data == ['foo']


def test_readables_from_paths_file(tmpdir):
    wexin = tmpdir.join('0.wexin')
    with wexin.open('w') as fp:
        fp.write('foo')
    data = []
    for readable in readables_from_paths([wexin.strpath]):
        data.append(read_chunks(readable))
    assert data == ['foo']


def test_chained_readable():
    reader = ChainedReadable(
        BytesIO(b'a'),
        BytesIO(b'b')
    )
    assert reader.read(3) == b'ab'


def test_chained_readable_is_pickleable():
    reader = ChainedReadable(
        BytesIO(b'a'),
        BytesIO(b'b')
    )
    reader2 = pickle.loads(pickle.dumps(reader))
    assert reader2.read(3) == b'ab'


def test_chained_readable_readline():
    reader = ChainedReadable(
        BytesIO(b'a'),
        BytesIO(b'b\nc')
    )
    assert reader.readline(10) == b'ab\n'


multiple_responses_ex1 = b'''HTTP/1.0 200 OK\r
Content-Length: 1\r
\r
foo\r
boundary\r
FTP/1.0 200 OK\r
\r
bar'''


def test_chained_readable_exhausted():
    reader = ChainedReadable(BytesIO(''))
    assert reader.readline() == b''
    assert reader.readline() == b''


def test_tee_readable(tmpdir):
    tmp = tmpdir.join('tmp')
    with open(tmp.strpath, 'w') as fp:
        reader = TeeReadable(BytesIO(b'abc'), fp)
        assert reader.read(10), b'abc'
        assert reader.name == tmp.strpath


def test_tee_readable_readline(tmpdir):
    tmp = tmpdir.join('tmp')
    with open(tmp.strpath, 'w') as fp:
        reader = TeeReadable(BytesIO(b'abc\n'), fp)
        assert reader.readline(10), b'abc\n'


def test_readables_from_file_path_where_path_is_tarfile():
    path = resource_filename(__name__, 'fixtures/example.tar')
    readables = readables_from_file_path(path)
    r0 = next(readables)
    r0p = pickle.loads(pickle.dumps(r0))
    assert r0p.readline() == 'HTTP/1.1 200 OK\n'


def test_partial_repr():
    class callme(object):
        def __call__(self):
            pass
        def __repr__(self):
            return 'callme'
    assert repr(partial_(callme(), 1, 2, 3)) == 'callme, (1, 2, 3)'


def test_open_repr():
    assert repr(Open(1)) == 'Open(1)'


def test_open_attribute_error():
    readable = Open('foo')
    with pytest.raises(AttributeError):
        readable.write


def test_tarfile_open_repeated_same_path():
    path = resource_filename(__name__, 'fixtures/example.tar')
    tf1 = tarfile_open(path)
    tf2 = tarfile_open(path)
    assert tf1 is tf2


def test_tarfile_open_repeated_different_path():
    path1 = resource_filename(__name__, 'fixtures/example.tar')
    path2 = resource_filename(__name__, 'fixtures/example2.tar')
    tf1 = tarfile_open(path1)
    tf2 = tarfile_open(path2)
    assert tf1 is not tf2
