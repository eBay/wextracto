""" Wextracto command line (console) entry point. """

from __future__ import absolute_import, unicode_literals, print_function
import argparse
from pkg_resources import resource_filename
from .readable import readables_from_paths
from .processpool import do
from .output import StdOut, TeeStdOut, write_values
from .value import Value
from .entrypoints import extractor_from_entry_points


default_logging_conf = resource_filename(__name__, 'logging.conf')


argparser = argparse.ArgumentParser()

argparser.add_argument(
    'paths',
    metavar='path',
    nargs='+',
    help="url, directory or file from which to extract"
)

process_pool_size = argparser.add_mutually_exclusive_group()

process_pool_size.add_argument(
    '-P',
    dest='process_pool_size',
    action="store_const",
    const=None,
    default=1,
    help="use multiprocessing pool",
)

process_pool_size.add_argument(
    '--process-pool',
    dest='process_pool_size',
    metavar='N',
    type=int,
    default=1,
    help="use multiprocessing pool with size of N",
)

argparser.add_argument(
    '--responses',
    dest="responses_dir",
    metavar="DIR",
    default="responses",
    help="use directory DIR for saved input and output",
)

argparser.add_argument(
    '-s', '--save',
    action='store_true',
    default=False,
    help="save response input and extraction output",
)

argparser.add_argument(
    '-x', '--exit-on-exc',
    action="store_true",
    default=False,
    help="exit when an exception occurs during extraction",
)



class WriteExtracted(object):

    def __init__(self, context, extract):
        self.context = context
        self.extract = extract

    def __call__(self, readable):
        return write_values(self.context, readable, self.extract)


def main():
    """ The main 'wex' command """

    import logging.config ; logging.config.fileConfig(default_logging_conf)

    args = argparser.parse_args()
    extract = extractor_from_entry_points()
    if args.save:
        func = WriteExtracted(TeeStdOut, extract)
    else:
        func = WriteExtracted(StdOut, extract)
    Value.exit_on_exc = args.exit_on_exc

    readables = readables_from_paths(args.paths, args.save, args.responses_dir)
    do(func, readables, pool_size=args.process_pool_size)
