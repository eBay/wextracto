from six.moves.html_parser import HTMLParser

replacements = {
    0x00: 0xFFFD,
    0x0D: 0x000D,
    0x80: 0x20AC,
    0x81: 0x0081,
    0x81: 0x0081,
    0x82: 0x201A,
    0x83: 0x0192,
    0x84: 0x201E,
    0x85: 0x2026,
    0x86: 0x2020,
    0x87: 0x2021,
    0x88: 0x02C6,
    0x89: 0x2030,
    0x8A: 0x0160,
    0x8B: 0x2039,
    0x8C: 0x0152,
    0x8D: 0x008D,
    0x8E: 0x017D,
    0x8F: 0x008F,
    0x90: 0x0090,
    0x91: 0x2018,
    0x92: 0x2019,
    0x93: 0x201C,
    0x94: 0x201D,
    0x95: 0x2022,
    0x96: 0x2013,
    0x97: 0x2014,
    0x98: 0x02DC,
    0x99: 0x2122,
    0x9A: 0x0161,
    0x9B: 0x203A,
    0x9C: 0x0153,
    0x9D: 0x009D,
    0x9E: 0x017E,
    0x9F: 0x0178,
}

class NumCharRefFixer(HTMLParser):

    join = b''.join

    def __init__(self, fp):
        HTMLParser.__init__(self)
        self.fp = fp
        self.replacement = None
        self.fixes = []

    def updatepos(self, i, j):
        if self.replacement:
            self.fixes.append((i, j, self.replacement))
            self.replacement = None
        return HTMLParser.updatepos(self, i, j)

    def handle_charref(self, name):
        if name.startswith('x'):
            code_point = int(name[1:], 16)
        else:
            code_point = int(name, 10)
        if code_point in replacements:
            self.replacement = (name, 'x%0X' % replacements[code_point])

    def read(self, size=None):
        chunks = []
        while True:
            new_data = self.fp.read(size)
            if not new_data:
                if self.rawdata:
                    raw_data = self.rawdata
                    self.close()
                    chunks.append(self.apply_fixes(raw_data))
                break
            raw_data = self.rawdata + new_data
            self.feed(new_data)
            chunks.append(self.apply_fixes(raw_data))
            if not size or sum(len(chunk) for chunk in chunks) >= size:
                break
        return self.join(chunks)

    def apply_fixes(self, data):
        start = 0
        parts = []
        limit = len(data) - len(self.rawdata)
        for i, j, (old, new) in self.fixes:
            if i > start:
                parts.append(data[start:i])
            parts.append(data[i:j].replace(old, new))
            start = j
        if start < limit:
            parts.append(data[start:limit])
        self.fixes = []
        return self.join(parts)
