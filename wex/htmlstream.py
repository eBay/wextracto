""" HTMLStream converts a byte stream in to a unicode stream for parsing. """

import codecs
from lxml.etree import XMLSyntaxError
from lxml.html import HTMLParser

CHUNK_SIZE = 1024
MAX_HEAD_CHUNKS = 50

#
# To process an HTML byte stream we need to know the character encoding.
# (often incorrectly called the charset.)
#
# Declarations of the encoding of an HTML document can be found:
#   * as a parameter in HTTP "Content-type" header
#   * in the "charset" attribute of an HTML <meta> tag
#   * in the "content" attribute of an HTML <meta> tag
#     with an "http-equiv" attribute of "content-type"
#
# Sometimes these will match, sometimes they will not.
# To find encodings in <meta> tags we need to pre-parse the document.


# stop pre-parsing if we reach any tags other than these
HEAD_TAGS = set([
    'html',
    'head',
    'title',
    'style',
    'base',
    'link',
    'meta',
    'script',
    'noscript',
])

# pre-parse this many bytes at a time
PRE_PARSE_CHUNK_SIZE = 4 * 1024

# stop pre-parsing if we have read this many bytes
MAX_PRE_PARSE_BYTES = 40 * 1024


# encodings where the (printable) characters are a superset
encoding_substitutions = {
    'gb2312': 'gbk',
    'iso8859-1': 'cp1252',
    'iso8859-9': 'cp1254',
}

#
# Take 10K random strings of 8 bytes each and
# see how many give you UnicodeDecode errors.
# Anything that isn't in the table gave 0.
ranking = {
    'cp1251': 3058,
    'iso8859-7': 9059,
    'cp1250': 14390,
    'cp1252': 14429,
    'cp1254': 19754,
    'iso8859-11': 22290,
    'tis-620': 24760,
    'cp1255': 52721,
    'shift_jis': 71873,
    'gbk': 74930,
    'big5': 90760,
    'euc_kr': 96158,
    'gb2312': 96714,
    'euc_jp': 96995,
    'utf-8': 99095,
    'ascii': 99627,
}


def content_type_encodings(content_type):
    # note: we have found at least one example with two "charset=" params
    #       where one was good and one was bad.
    #       HTTPMessage.get_content_charset() just takes the
    #       first, but actually we might as well try them all.
    for param in content_type.split(';')[1:]:
        key, _, value = param.partition('=')
        if key.strip().lower() == 'charset':
            yield value.strip()


class HTMLStream(object):

    def __init__(self, response, filename=None):
        self.filename = filename
        self.encodings = []
        self.response = response
        self.declared_encodings = self.find_declared_encodings()
        self.decoders = self.yield_decoders()
        self.decoded = u''
        self.encoding, self.decoder = next(self.decoders)

    def find_declared_encodings(self):
        encodings = []
        content_type = self.response.headers.get('content-type', '')
        encodings.extend(content_type_encodings(content_type))
        encodings.extend(self.parse_head())
        return encodings

    def ranked_encodings(self):
        """ Declared encodings ranked by order of resistance to errors. """
        def lookup(encoding):
            try:
                name = codecs.lookup(encoding).name
                return encoding_substitutions.get(name, name)
            except LookupError:
                return None

        normalized = filter(None,
                            (lookup(enc) for enc in self.declared_encodings))

        # of the declared encodings we want to try the most resilient to
        # errors first.
        ranked = sorted(normalized,
                        key=lambda enc: ranking.get(enc, 0),
                        reverse=True)
        return ranked

    def yield_decoders(self):

        ranked_encodings = self.ranked_encodings()

        for encoding in ranked_encodings:
            info = codecs.lookup(encoding)
            decoder = info.incrementaldecoder()
            yield info.name, decoder

        if 'utf-8' not in ranked_encodings:
            info = codecs.lookup('utf-8')
            yield info.name, info.incrementaldecoder()

        # character set detection could go here
        if ranked_encodings:
            fallback = codecs.lookup(ranked_encodings[0])
        else:
            fallback = codecs.lookup('cp1252')

        # for our fallback we 'replace' errors
        yield fallback.name, fallback.incrementaldecoder('replace')

    def next_encoding(self):
        self.response.seek(0)
        self.decoded = u''
        self.encoding, self.decoder = next(self.decoders)

    def read(self, size=None):
        while True:
            raw_bytes = self.response.read(size)
            if not raw_bytes:
                # tell the decoder to flush
                self.decoded += self.decoder.decode(raw_bytes, True)
                break
            self.decoded += self.decoder.decode(raw_bytes)
            if size is None or len(self.decoded) >= size:
                break
        decoded = self.decoded[:size]
        self.decoded = self.decoded[len(decoded):]
        return decoded

    def parse_head(self):
        meta = HTMLMetaEncodings()
        # parser will fail on non-ascii unless we set it explicitly
        parser = HTMLParser(target=meta, encoding='ISO-8859-1')
        meta.parser = parser
        total_bytes = 0
        while meta:
            chunk = self.response.read(PRE_PARSE_CHUNK_SIZE)
            if not chunk:
                try:
                    parser.close()
                except XMLSyntaxError:
                    pass
                break
            parser.feed(chunk)
            total_bytes += len(chunk)
            if total_bytes >= MAX_PRE_PARSE_BYTES:
                break
        self.response.seek(0)
        return meta.encodings


class HTMLMetaEncodings(object):

    def __init__(self):
        self.encodings = []
        self.more = True

    def __bool__(self):
        return self.more

    def start(self, tag, attrib):
        if tag not in HEAD_TAGS:
            # we don't want any more chunks
            self.more = False
        elif tag == 'meta':
            if 'charset' in attrib:
                self.encodings.append(attrib['charset'])
            elif attrib.get('http-equiv', '').lower() == 'content-type':
                content_type = attrib.get('content', '')
                self.encodings.extend(content_type_encodings(content_type))

    def close(self):
        pass
