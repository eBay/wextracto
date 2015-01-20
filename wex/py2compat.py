""" Compatability fixes to make Python 2.7 look more like Python 3.

The general approach is to code using the common subset offered by 'six'.

The HTTPMessage class has a different interface.  This work-arounds makes the
Python 2.7 look enough like the Python 3 for the Wextracto code to work.
"""

import six

if six.PY2:

    from httplib import HTTPMessage

    def get_content_subtype(self):
        return self.getsubtype()
    HTTPMessage.get_content_subtype = get_content_subtype

    def get_content_charset(self):
        return self.getparam('charset')
    HTTPMessage.get_content_charset = get_content_charset


    def parse_headers(fp):
        return HTTPMessage(fp, 0)

else:

    from http.client import parse_headers  # pragma: no cover
    assert parse_headers                   # pragma: no cover
