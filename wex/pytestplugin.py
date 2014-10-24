from __future__ import absolute_import, unicode_literals, print_function  # pragma: no cover

#
# pytest-cov reports missing coverage when things are imported *before*
# the testing has started.  That is why this module is filled with 
# function level imports and pragmas.
#

import io
import codecs
import pytest                                            # pragma: no cover

TAB = '\t'  # pragma: no cover
LF = '\n'  # pragma: no cover
MISSING = object()  # pragma: no cover

def pytest_collect_file(parent, path):                   # pragma: no cover
    from .readable import EXT_WEXIN
    if path.check(ext=EXT_WEXIN.lstrip('.')):
        return WexinFile(path, parent)


class WexinFile(pytest.File):                        # pragma: no cover
    """ A .wexin file is a stored response. """

    def __init__(self, path, parent):
        super(WexinFile, self).__init__(path, parent)
        self.actual = None

    def collect(self):                                   # pragma: no cover
        from itertools import groupby
        from .output import EXT_WEXOUT
        basename = self.fspath.purebasename + EXT_WEXOUT
        wexout = self.fspath.dirpath().join(basename)
        items = (line.rstrip(LF).split(TAB) for line in codecs.open(wexout.strpath, encoding='UTF-8'))
        keys = set()
        for key, items_for_key in groupby(items, key=lambda item: tuple(item[:-1])):
            values = set()
            keys.add(key)
            for item in items_for_key:
                values.add(item[-1])
            yield WextractoItem(key, self, values)

    def get_actual(self, key, default=MISSING):
        if self.actual is None:
            self.actual = self.extract()
        return self.actual.get(key, default)

    def extract(self):
        from .extractor import ExtractorFromEntryPoints
        from .response import Response
        from .value import json_encode
        #from .output import encoder
        values = {}
        extract = ExtractorFromEntryPoints()
        with self.fspath.open('rb') as readable:
            for value in Response.values_from_readable(extract, readable):
                value_set = values.setdefault(value.labels, set())
                try:
                    value_set.add(json_encode(value.value))
                except TypeError:
                    pass
        return values


class WextractoItem(pytest.Item):                        # pragma: no cover
    def __init__(self, key, parent, values):            # pragma: no cover
        super(WextractoItem, self).__init__('::'.join(key), parent)
        self.key = key
        self.values = values

    def runtest(self):
        actual = self.parent.get_actual(self.key, MISSING)
        assert actual is not MISSING
        assert actual == self.values
