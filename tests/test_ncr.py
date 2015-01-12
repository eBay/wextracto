# -*- coding: utf-8 -*-
from six import BytesIO
from wex import ncr

script = b"""
<script src="/foo">
    var my_html = "</p>";
    var x = "&#x95;":
</script>
"""

def test_end_char_ref():
    assert ncr.end_char_ref.search(b'#123;').group(1) == '123'


def test_end_char_ref_entity():
    assert ncr.end_char_ref.search(b'amp;').group(1) == None


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


def test_ncr_decimal():
    content = ncr.InvalidNumCharRefReplacer(BytesIO(b"&#149;"))
    assert content.read() == b"&#x2022;"


def test_ncr_empty():
    content = ncr.InvalidNumCharRefReplacer(BytesIO(b"&#;"))
    assert content.read() == b"&#;"


def test_ncr_script():
    content = ncr.InvalidNumCharRefReplacer(BytesIO(script))
    assert content.read() == script


def test_ncr_no_semi_colon_terminated():
    content = ncr.InvalidNumCharRefReplacer(BytesIO('&#x95,45'))
    assert content.read() == b"&#x2022,45"
