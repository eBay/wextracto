# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from io import StringIO
from wex import ncr

script = """
<script src="/foo">
    var my_html = "</p>";
    var x = "&#x95;":
</script>
"""

elem = "<code>Hello &#x95;</code>"


def test_end_char_ref():
    assert ncr.end_char_ref.search('#123;').group(1) == '123'


def test_end_char_ref_entity():
    assert ncr.end_char_ref.search('amp;').group(1) is None


def test_clean_ncr():
    assert ncr.clean_ncr('&#x95;', True) == ("&#x2022;", '', None)


def test_clean_ncr_script_cdata():
    assert ncr.clean_ncr(script, True) == (script, '', None)


def test_clean_ncr_partial_script():
    html = script[:script.find('</')]
    assert ncr.clean_ncr(html, True) == (html, '', 'script')


def test_ncr():
    content = ncr.InvalidNumCharRefReplacer(StringIO("&#x95;"))
    assert content.read() == "&#x2022;"


def test_ncr_decimal():
    content = ncr.InvalidNumCharRefReplacer(StringIO("&#149;"))
    assert content.read() == "&#x2022;"


def test_ncr_empty():
    content = ncr.InvalidNumCharRefReplacer(StringIO("&#;"))
    assert content.read() == "&#;"


def test_ncr_script():
    content = ncr.InvalidNumCharRefReplacer(StringIO(script))
    assert content.read() == script


def test_ncr_no_semi_colon_terminated():
    content = ncr.InvalidNumCharRefReplacer(StringIO('&#x95,45'))
    assert content.read() == "&#x2022,45"


def test_ncr_bug_read_with_size():
    content = ncr.InvalidNumCharRefReplacer(StringIO(elem))
    assert content.read(26) == "<code>Hello &#x2022;</code"
    assert content.read(26) == ">"


def test_read_less_that_whole_token():
    content = ncr.InvalidNumCharRefReplacer(StringIO(elem))
    assert content.read(2) == "<c"
    assert content.read() == "ode>Hello &#x2022;</code>"


def test_replace_invalid_ncr():
    content = ncr.replace_invalid_ncr(StringIO(elem))
    assert content.read() == "<code>Hello &#x2022;</code>"
