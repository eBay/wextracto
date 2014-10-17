import os
import errno
import pytest
from six import next, BytesIO
from wex.readable import EXT_WEXIN
#from wex.save import save_url_from_path, save_output_from_readable

#
#
#def read_chunks(readable, size=2**16):
#    chunks = []
#    while True:
#        chunk = readable.read(size)
#        if not chunk:
#            break
#        chunks.append(chunk)
#    return b''.join(chunks)
#
#
#def test_save_url_from_path(tmpdir):
#    url_from_path = save_url_from_path(tmpdir.strpath)
#    url = url_from_path('http://httpbin.org/get?this=that')
#    for readable in url.get():
#        read_chunks(readable)
#    files = [os.path.join(dirpath, filename) 
#             for dirpath, dirnames, filenames in os.walk(tmpdir.strpath)
#             for filename in filenames]
#    assert len(files) == 1
#    assert os.path.basename(files[0]) == '0' + EXT_WEXIN
#
#
#def test_save_url_from_path_oserror(tmpdir):
#    ro = tmpdir.mkdir('ro')
#    st = os.stat(ro.strpath)
#    os.chmod(ro.strpath, 0444)
#    try:
#        url_from_path = save_url_from_path(ro.strpath)
#        url = url_from_path('http://httpbin.org/get?this=that')
#        with pytest.raises(OSError) as excinfo:
#            next(url.get())
#    finally:
#        # Need to change it back or else it won't get cleaned up :(
#        os.chmod(ro.strpath, st.st_mode)
#    assert excinfo.value.errno == errno.EACCES
#
#
#def test_save_output_from_readable(tmpdir):
#    stdout = BytesIO()
#    wexin = tmpdir.join('0.wexin')
#    wexout = tmpdir.join('0.wexout')
#    with wexin.open('w') as fp:
#        fp.write('foo')
#    with save_output_from_readable(wexin.open('r'), stdout) as write:
#        write(('this', 'that'))
#    assert wexout.open('r').read() == 'this\t"that"\n'
#
#
#def test_save_output_from_readable_no_name(tmpdir):
#    stdout = BytesIO()
#    readable = BytesIO('foo')
#    with save_output_from_readable(readable, stdout) as write:
#        write(('this', 'that'))
