# -*- coding: utf-8 -*-
from six import BytesIO
from wex import ncr

script = b"""
<script src="/foo">
    var x = "&#x95;":
</script>
"""

def test_clean_ncr():
    assert ncr.clean_ncr(b'&#x95;', True) == (b"&#x2022;", b'', None)


def test_clean_ncr_script_cdata():
    assert ncr.clean_ncr(script, True) == (script, b'', None)


def test_clean_ncr_partial_script():
    html = script[:script.find(b'</')]
    assert ncr.clean_ncr(html, True) == (html, b'', b'script')


def test_ncr():
    content = ncr.InvalidNumCharRefReplacer(BytesIO(b"&#x95;"))
    assert content.read() == b"&#x2022;"


def test_ncr_script():
    content = ncr.InvalidNumCharRefReplacer(BytesIO(script))
    assert content.read() == script
#
#
#def test_ncr_incremental():
#    content = NumCharRefFixer(BytesIO(b"<div>&#x95;</div>"))
#    assert content.read(5) == b"<div>"
#    assert content.read(5) == b"&#x2022;"
#    assert content.read(5) == b"</div>"
#    assert content.read(5) == b""
