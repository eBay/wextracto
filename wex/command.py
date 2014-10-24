""" Wextracto command line (console) entry point. """

from __future__ import absolute_import, unicode_literals, print_function
import argparse
from pkg_resources import resource_filename
from .readable import readables_from_paths
from .processpool import do
from .extractor import ExtractorFromEntryPoints
from . import output


default_logging_conf = resource_filename(__name__, 'logging.conf')


argparser = argparse.ArgumentParser()

argparser.add_argument(
    'paths',
    metavar='path',
    nargs='+',
    help="paths (urls, directories, files) from which to extract data"
)

argparser.add_argument(
    '-s', '--save',
    action='store_true',
    default=False,
    help="save response input and extraction output",
)

argparser.add_argument(
    '--responses',
    dest="responses_dir",
    default="responses",
    help="Directory for saved input and output",
)

argparser.add_argument(
    '-P', '--process-pool',
    action="store",
    metavar="SIZE",
    const=None,
    nargs='?',
    type=int,
    default=1,
    help="Use multi-process pool, optionally specificying size",
)

argparser.add_argument(
    '-x', '--exclude-entry-point',
    action="append",
    default=[],
    dest="excluded_entry_points",
    help="Exclude extractor(s) with this entry point name"
)


class WriteExtracted(object):

    def __init__(self, write, extract):
        self.write = write
        self.extract = extract

    def __call__(self, readable):
        return self.write(self.extract, readable)


def main():
    """ The main 'wex' command """

    import logging.config ; logging.config.fileConfig(default_logging_conf)

    args = argparser.parse_args()
    extract = ExtractorFromEntryPoints(args.excluded_entry_points)
    if args.save:
        func = WriteExtracted(output.write_values_to_stdout_and_dir, extract)
    else:
        func = WriteExtracted(output.write_values_to_stdout, extract)

    readables = readables_from_paths(args.paths, args.save, args.responses_dir)
    do(func, readables, pool_size=args.process_pool)
