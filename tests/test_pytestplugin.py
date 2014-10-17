from six import next
from pkg_resources import resource_filename, working_set
from wex.readable import EXT_WEXIN
from wex.output import EXT_WEXOUT
from wex import pytestplugin

def pytest_funcarg__parent(request):
    return request.session

response = b"""HTTP/1.1 200 OK\r
Content-type: application/json\r
\r
{"args":{"this":"that"}}"""


def setup_module():
    entry = resource_filename(__name__, 'fixtures/TestMe.egg')
    working_set.add_entry(entry)


def test_pytest_collect_file(tmpdir, parent):
    # FTM just to see how to coverage test the plugin
    r0_wexin = tmpdir.join('0' + EXT_WEXIN)
    r0_wexout = tmpdir.join('0' + EXT_WEXOUT)
    with r0_wexin.open('w') as fp:
        fp.write(response)
    with r0_wexout.open('w') as fp:
        fp.write('this\t"that"\n')
    fileobj = pytestplugin.pytest_collect_file(parent, r0_wexin)
    item = next(fileobj.collect())
    item.runtest()
