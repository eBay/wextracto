from six import PY2
from six.moves.http_client import HTTPMessage


if PY2:
    HTTPMessage.get_content_subtype = (lambda self: self.getsubtype())
    HTTPMessage.get_content_charset = (lambda self: self.getparam('charset'))
