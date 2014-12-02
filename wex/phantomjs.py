import os
import subprocess
import tempfile
import json
from contextlib import closing
from pkg_resources import resource_filename

js = os.path.abspath(resource_filename(__name__, 'phantomjs.js'))
cmd = ['phantomjs', '--disk-cache=true', js]
#cmd = ['phantomjs', js]

def request(url, method, session=None, **kw):
    phantomjs = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    path = os.path.join(tempfile.gettempdir(),
                        'wex.phantomjs.{}.fifo'.format(os.getpid()))
    os.mkfifo(path)
    # PhantomJS seems to send the fragment and we don't want that
    url = dict(url=url.partition('#')[0], wex_url=url, wexout=path)
    phantomjs.stdin.write(json.dumps(url) + "\n")
    phantomjs.stdin.flush()
    with closing(open(path, 'r')) as readable:
        yield readable

if __name__ == '__main__':
    import sys
    for url in sys.argv[1:]:
        for readable in request(url, None):
            sys.stdout.write(readable.read())

