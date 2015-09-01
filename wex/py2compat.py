""" Compatability fixes to make Python 2.7 look more like Python 3.

The general approach is to code using the common subset offered by 'six'.

The HTTPMessage class has a different interface.  This work-arounds makes the
Python 2.7 look enough like the Python 3 for the Wextracto code to work.
"""

import six

if six.PY2:

    import urllib
    import tarfile
    from httplib import HTTPMessage

    def get_content_subtype(self):
        return self.getsubtype()
    HTTPMessage.get_content_subtype = get_content_subtype

    def get_content_charset(self):
        return self.getparam('charset')
    HTTPMessage.get_content_charset = get_content_charset

    def parse_headers(fp):
        return HTTPMessage(fp, 0)

    def urlquote(name, *args, **kwargs):
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        return urllib.quote(name, *args, **kwargs)

    def xzopen(cls, name, mode="r", fileobj=None, compresslevel=9, **kwargs):
        """Open lzma compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w"):
            raise ValueError("mode must be 'r' or 'w'")

        try:
            from backports import lzma
            lzma.LZMAFile
        except (ImportError, AttributeError):
            raise tarfile.CompressionError("lzma module is not available")

        try:
            fileobj = lzma.LZMAFile(fileobj or name, mode)
        except (OSError, IOError):
            if mode == 'r':
                raise tarfile.ReadError("not an lzma file")
            raise

        try:
            fileobj.peek()
        except (lzma.LZMAError, EOFError):
            raise tarfile.ReadError("not an lzma file")

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except IOError:
            fileobj.close()
            if mode == 'r':
                raise tarfile.ReadError("not an lzma file")
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    tarfile.TarFile.xzopen = classmethod(xzopen)
    tarfile.TarFile.OPEN_METH['xz'] = 'xzopen'

else:

    from http.client import parse_headers  # pragma: no cover
    assert parse_headers                   # pragma: no cover

    from six.moves.urllib_parse import quote as urlquote
    assert urlquote
