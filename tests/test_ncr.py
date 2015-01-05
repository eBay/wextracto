# -*- coding: utf-8 -*-
from six import BytesIO
from wex.ncr import NumCharRefFixer


def test_ncr():
    content = NumCharRefFixer(BytesIO(b"&#x95;"))
    assert content.read() == "&#x2022;"


def test_ncr_incremental():
    content = NumCharRefFixer(BytesIO(b"<div>&#x95;</div>"))
    assert content.read(5) == "<div>"
    assert content.read(5) == "&#x2022;"
    assert content.read(5) == "</div>"
    assert content.read(5) == ""
