import os
import logging
import json
from six import binary_type
from threading import Timer
from subprocess import Popen, PIPE
from pkg_resources import resource_filename


script = os.path.abspath(resource_filename(__name__, 'js/phantom.js'))
cmd = ['phantomjs', script]
# see http://phantomjs.org/api/webpage/property/settings.html
default_settings = {'loadImages': False}


def request_using_phantomjs(url, method, session=None, **kw):

    phantomjs = Popen(cmd, stdin=PIPE, stdout=PIPE)

    def terminate_phantomjs():
        if phantomjs.poll() is not None:
            return
        phantomjs.terminate()
        logging.getLogger(__name__).warning("phantomjs terminated")

    timeout_timer = Timer(10.0, terminate_phantomjs)

    settings = dict(default_settings)
    settings.update(method.args.get('settings', {}))
    requires = []
    for require in method.args.get('requires', []):
        if isinstance(require, (tuple, list)):
            stem, _ = os.path.splitext(resource_filename(*require))
            requires.append(stem)
        else:
            requires.append(require)

    request = {"url": url, "requires": requires, "settings": settings}
    dumped = json.dumps(request)
    if not isinstance(dumped, binary_type):
        dumped = dumped.encode('utf-8')
    phantomjs.stdin.write(dumped)
    phantomjs.stdin.close()
    timeout_timer.start()
    yield phantomjs.stdout
    timeout_timer.cancel()
