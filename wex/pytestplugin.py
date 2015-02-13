""" When maintaining extractors it can be helpful to have some sample input
and output so that regression testing can be performed when we need to change
the extractors.

Wextracto supports this by using the ``--save`` or ``--save-dir`` options to
the :mod:`wex <wex.command>` command.  This option saves both the input and
output to a local directory.

This input and output can then be used for comparison with the current
extractor output.

To check compare current output against saved output run 
`py.test <http://pytest.org/>`_ like so:

.. code-block:: shell

    $ py.test saved/


"""
from __future__ import absolute_import, unicode_literals, print_function  # pragma: no cover

#
# pytest-cov reports missing coverage when things are imported *before*
# the testing has started.  That is why this module is filled with 
# function level imports and pragmas.
#

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
        self.extracted_values = None
        self.value_items = {}

    def collect(self):                                   # pragma: no cover
        from .output import EXT_WEXOUT
        basename = self.fspath.purebasename + EXT_WEXOUT
        path = self.fspath.dirpath().join(basename)
        self.value_items = {}
        with path.open(encoding='UTF-8') as wexout:
            # For testing purposes we keep the values as JSON strings
            # this lets us not have to worry about hashable types, etc.
            for line in wexout:
                labels, _, value = line.rpartition('\t')
                if labels in self.value_items:
                    item = self.value_items[labels]
                else:
                    item = WexoutValues(labels, self)
                    self.value_items[labels] = item
                    yield item
                item.values.add(value.strip())
        yield WexoutLabels('labels', self)

    def get_extracted_values(self, name):
        if self.extracted_values is None:
            self.extracted_values = self.extract_values()
        return self.extracted_values.get(name, set())

    def get_extracted_labels(self):
        if self.extracted_values is None:
            self.extracted_values = self.extract_values()
        return set(self.extracted_values)

    def extract_values(self):
        from .entrypoints import extractor_from_entry_points
        from .response import Response
        values = {}
        extract = extractor_from_entry_points()
        with self.fspath.open('rb') as readable:
            for value in Response.values_from_readable(extract, readable):
                for line in value.text():
                    labels, _, value = line[:-1].rpartition(TAB)
                    values.setdefault(labels, set()).add(value)
        return values


class WexoutValues(pytest.Item):                        # pragma: no cover
    """ Test that the value set is the same. """

    def __init__(self, name, parent):            # pragma: no cover
        super(WexoutValues, self).__init__(name, parent)
        self.values = set()

    def runtest(self):
        assert self.values == self.parent.get_extracted_values(self.name)


class WexoutLabels(pytest.Item):
    """ Test that we still see the same set of labels. """

    def runtest(self):
        extracted_labels = self.parent.get_extracted_labels()
        saved_labels = set(self.parent.value_items.keys())
        assert extracted_labels == saved_labels
