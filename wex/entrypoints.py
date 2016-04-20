""" The simplest way to register :mod:`extractors <wex.extractor>` is to have 
a file named ``entry_points.txt`` in the current directory.  This file should 
look something like this:

.. code-block:: cfg

    [wex]
    .example.net = mymodule:extract_from_example_net

The ``[wex]`` section heading tells Wextracto that
the following lines register extractors.

Extractors are registered using ``name = value`` pairs.
If the name starts with ``.`` then the extractor is only applied to 
responses from 
`domain names <http://en.wikipedia.org/wiki/Domain_name>`_
that match that name.
Our example would match responses from ``www.example.net`` or ``example.net``.

If the name does not start with ``.`` it will be applied responses whatever
their domain.

You can register the same extractor against multiple domain names by 
having multiple lines with the same value but different names.

This is exactly the same format and content that you would use in the 
``entry_points`` parameter for a 
`setup function <https://pythonhosted.org/setuptools/setuptools.html#new-and-changed-setup-keywords>`_, 
if and when you want to package and your extractor functions.
"""

from __future__ import absolute_import, unicode_literals, print_function
import sys
import os
import logging
import errno
from pkg_resources import EntryPoint, iter_entry_points
from six.moves.urllib_parse import urlparse
from six import itervalues
from wex.extractor import Chained


GROUP='wex'


def get_wex_entry_points_from_cwd():
    try:
        with open(os.path.join(os.getcwd(), 'entry_points.txt')) as txt:
            entry_point_map = EntryPoint.parse_map(txt.read())
        entry_points = {str(ep): ep
                        for ep in entry_point_map.get(GROUP, {}).values()}
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
    except IOError as exc:
        if exc.errno != errno.ENOENT:
            raise
        entry_points = {}

    return entry_points


class ExtractorFromEntryPoints(object):
    """ An extractor combining extractors loaded from entry points. """

    def __init__(self):
        self.extractors = {}
        self.wex_entry_points_from_cwd = get_wex_entry_points_from_cwd()

    def __call__(self, arg0, *args, **kw):
        hostname = urlparse(getattr(arg0, 'url', '') or '').hostname
        if hostname not in self.extractors:
            self.extractors[hostname] = self.load_extractor(hostname)
        extractor = self.extractors[hostname]
        return extractor(arg0, *args, **kw)

    def load_extractor(self, hostname):
        extractors = []
        for ep in self.iter_wex_entry_points():
            if ep.name.startswith('.') and not domain_suffix(ep, hostname):
                continue
            append_if_load_succeeded(extractors, ep)
        return Chained(*extractors)

    def iter_wex_entry_points(self):

        for ep in iter_entry_points(GROUP):
            # we don't want to load the same entry point twice
            if str(ep) in self.wex_entry_points_from_cwd:
                continue
            yield ep

        for ep in itervalues(self.wex_entry_points_from_cwd):
            yield ep


def extractor_from_entry_points():
    return ExtractorFromEntryPoints()


def domain_suffix(entry_point, name):
    return name and ('.' + name).endswith(entry_point.name)


def append_if_load_succeeded(extractors, entry_point):
    try:
        extractors.append(entry_point.load(False))
    except Exception:
        logger = logging.getLogger(__name__)
        logger.exception("Failed to load [%s] entry point '%s'",
                         GROUP, entry_point.name)

