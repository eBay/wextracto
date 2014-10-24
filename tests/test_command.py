from __future__ import unicode_literals, print_function
import os
import sys
import subprocess
from itertools import tee
from six.moves import zip
from pkg_resources import working_set, resource_filename
import pytest
from wex.url import URL
from wex import command


url = URL('http://httpbin.org/get?this=that')


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def setup_module():
    entry = resource_filename(__name__, 'fixtures/TestMe.egg')
    working_set.add_entry(entry)


def find_file_paths(top):
    paths = []
    for dirpath, dirs, filenames in os.walk(top):
        paths.extend(os.path.join(dirpath, filename) for filename in filenames)
    return set(paths)


def Xtest_main(monkeypatch, capsys):
    argv = sys.argv[:1] + [url]
    monkeypatch.setattr(sys, 'argv', argv)
    command.main()
    out, err = capsys.readouterr()
    assert out == 'this\t"that"\n'


def Xtest_console_script():
    env = dict(os.environ)
    egg = resource_filename(__name__, 'fixtures/TestMe.egg')
    env['PYTHONPATH'] = egg
    exe = os.path.join(os.path.dirname(sys.executable), 'wex')
    # this url is cunningly crafted to generate UTF-8 output
    url = 'http://httpbin.org/get?this=that%C2%AE'
    cmd = [exe, url]
    wex = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
    output = wex.stdout.read()
    assert wex.wait() == 0
    assert output == b'this\t"that\xc2\xae"\n'



def Xtest_main_tarfile(monkeypatch, capsys):
    example_tar = resource_filename(__name__, 'fixtures/example.tar')
    argv = sys.argv[:1] + [example_tar]
    monkeypatch.setattr(sys, 'argv', argv)
    command.main()
    out, err = capsys.readouterr()
    assert out == 'this\t"that"\n'


def Xtest_main_save(monkeypatch, tmpdir, capsys):
    destdir = tmpdir.strpath
    argv = sys.argv[:1] + ['--save', '--responses', destdir, url]
    monkeypatch.setattr(sys, 'argv', argv)

    command.main()
    sentinel = object()
    expected_dirs = [
        'http',
        'httpbin.org',
        'get',
        'this%3Dthat',
        '178302e981e586827bd8ca962c1c27f8',
        sentinel
    ]
    dirpath = destdir
    for dirname, subdir in pairwise(expected_dirs):
        dirpath = os.path.join(dirpath, dirname)
        if subdir is not sentinel:
            assert os.listdir(dirpath) == [subdir]
    assert sorted(os.listdir(dirpath)) == ['0.wexin', '0.wexout']
    out, err = capsys.readouterr()
    assert out == 'this\t"that"\n'


def Xtest_main_no_such_file(monkeypatch, capsys):
    argv = sys.argv[:1] + ['no-such-file']
    monkeypatch.setattr(sys, 'argv', argv)
    with pytest.raises(SystemExit):
        command.main()
    out, err = capsys.readouterr()
    expected = "ERROR [wex.output] reading "
    assert err[:len(expected)] == expected
