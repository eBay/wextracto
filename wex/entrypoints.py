""" Loading, combining and using extractor functions """

from __future__ import absolute_import, unicode_literals, print_function
import sys
import os
import logging
import errno
from pkg_resources import EntryPoint, iter_entry_points
from six.moves.urllib_parse import urlparse
from six import itervalues
from wex.extractor import chained


GROUP='wex'


def get_wex_entry_points_from_cwd():
    try:
        with open(os.path.join(os.getcwd(), 'entry_points.txt')) as txt:
            entry_point_map = EntryPoint.parse_map(txt.read())
        entry_points = {str(ep): ep for ep in entry_point_map[GROUP].values()}
        if os.getcwd() not in sys.path:
            sys.path.insert(0, os.getcwd())
    except IOError as exc:
        if exc.errno != errno.ENOENT:
            raise
        entry_points = {}

    return entry_points


wex_entry_points_from_cwd = get_wex_entry_points_from_cwd()


class ExtractorFromEntryPoints(object):
    """ An extractor combining extractors loaded from entry points. """

    def __init__(self):
        self.extractors = {}

    def __call__(self, arg0, *args, **kw):
        hostname = urlparse(getattr(arg0, 'url', '') or '').hostname
        if hostname not in self.extractors:
            self.extractors[hostname] = self.load_extractor(hostname)
        extractor = self.extractors[hostname]
        return extractor(arg0, *args, **kw)

    def load_extractor(self, hostname):
        extractors = []
        for ep in iter_wex_entry_points():
            if ep.name.startswith('.') and not domain_suffix(ep, hostname):
                continue
            append_if_load_succeeded(extractors, ep)
        return chained(*extractors)


def extractor_from_entry_points():
    return ExtractorFromEntryPoints()


def iter_wex_entry_points():

    for ep in iter_entry_points(GROUP):
        # we don't want to load the same entry point twice
        if str(ep) in wex_entry_points_from_cwd:
            continue
        yield ep

    for ep in itervalues(wex_entry_points_from_cwd):
        yield ep


def domain_suffix(entry_point, name):
    return name and ('.' + name).endswith(entry_point.name)


def append_if_load_succeeded(extractors, entry_point):
    try:
        extractors.append(entry_point.load(False))
    except Exception:
        logger = logging.getLogger(__name__)
        logger.exception("Failed to load [%s] entry point '%s'",
                         GROUP, entry_point.name)

