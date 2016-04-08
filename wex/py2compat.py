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

    import http.client
    import email.parser

    def parse_headers(fp, _class=http.client.HTTPMessage):
        """Parses only RFC2822 headers from a file pointer.

        email Parser wants to see strings rather than bytes.
        But a TextIOWrapper around self.rfile would buffer too many bytes
        from the stream, bytes which we later need to read as bytes.
        So we read the correct bytes here, as bytes, for email Parser
        to parse.

        """
        headers = []
        _MAXLINE = http.client._MAXLINE
        _MAXHEADERS = http.client._MAXHEADERS
        while True:
            line = fp.readline(_MAXLINE + 1)
            if len(line) > _MAXLINE:
                raise http.client.LineTooLong("header line")
            headers.append(line)
            if len(headers) > _MAXHEADERS:
                raise http.client.HTTPException("got more than %d headers" % _MAXHEADERS)
            if line in (b'\r\n', b'\n', b''):
                break
        # hstring = b''.join(headers).decode('iso-8859-1')
        hstring = b''.join(headers).decode('utf-8')
        return email.parser.Parser(_class=_class).parsestr(hstring)


    from six.moves.urllib_parse import quote as urlquote
    assert urlquote
