from __future__ import unicode_literals
import os
import logging
import json
from six import binary_type, BytesIO
from six.moves.urllib_parse import urlparse
from threading import Timer
from subprocess import Popen, PIPE
from pkg_resources import resource_filename

DEFAULT_TIMEOUT = 60.0

script = os.path.abspath(resource_filename(__name__, 'js/phantom.js'))
cmd = ['phantomjs', '--ssl-protocol=any', script]
# see http://phantomjs.org/api/webpage/property/settings.html
default_settings = {'loadImages': False}

phantomjs_timeout = """HTTP/1.1 502 PhantomJS timeout
X-wex-request-url: {}

"""


class StdOutForPhantomJS(object):
    """ Handle timeout by generateding a failure. """

    def __init__(self, stdout, request_url):
        self.any_lines = False
        self.stdout = stdout
        self.failure = None
        self.request_url = request_url

    def readline(self, *args):

        if self.failure:
            return self.failure.readline(*args)

        line = self.stdout.readline(*args)
        if not line:
            if not self.any_lines:
                self.failure = self.create_timeout_fileobj(self.request_url)
                line = self.failure.readline(*args)
        else:
            self.any_lines = True

        return line

    def read(self, *args):
        if self.failure:
            return self.failure.read(*args)
        return self.stdout.read(*args)

    def create_timeout_fileobj(self, request_url):
        response = phantomjs_timeout.format(request_url)
        return BytesIO(response.encode('utf-8'))

    def close(self):
        self.stdout.close()

    @property
    def closed(self):
        return self.stdout.closed


def request_using_phantomjs(url, method, session=None, **kw):

    phantomjs = Popen(cmd, stdin=PIPE, stdout=PIPE)

    proxies = kw.get('proxies', None)
    if proxies:
        # only 'http' proxies for now
        proxy_url = proxies['http']
        parsed = urlparse(proxy_url)
        proxy = {
            'type': 'http',
            'hostname': parsed.hostname,
            'port': parsed.port or 80,
            'username': parsed.username,
            'password': parsed.password,
        }
    else:
        proxy = None

    def terminate_phantomjs():
        if phantomjs.poll() is not None:
            return
        phantomjs.terminate()
        logging.getLogger(__name__).warning("phantomjs terminated by timeout")

    timeout = method.args.get('timeout', DEFAULT_TIMEOUT)
    timeout_timer = Timer(timeout, terminate_phantomjs)

    settings = dict(default_settings)
    for key in ['WEX_PHANTOMJS_USER_AGENT', 'WEX_USER_AGENT']:
        if key in os.environ:
            settings['userAgent'] = os.environ[key]
            break

    settings.update(method.args.get('settings', {}))
    requires = []
    for require in method.args.get('requires', []):
        if isinstance(require, (tuple, list)):
            stem, _ = os.path.splitext(resource_filename(*require))
            requires.append(stem)
        else:
            requires.append(require)

    request = {
        "url": url,
        "requires": requires,
        "settings": settings,
        "loglevel": logging.getLogger(__name__).getEffectiveLevel(),
        "context": kw.get("context", {}),
        "proxy": proxy,
        "args": method.args,
    }
    dumped = json.dumps(request)
    if not isinstance(dumped, binary_type):
        # Python 3 json.dumps produces unicode, but stdin needs binary
        dumped = dumped.encode('utf-8')
    phantomjs.stdin.write(dumped)
    phantomjs.stdin.close()
    timeout_timer.start()
    try:
        yield StdOutForPhantomJS(phantomjs.stdout, url)
    finally:
        timeout_timer.cancel()
