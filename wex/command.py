""" Wextracto command line (console) entry point. """

from __future__ import absolute_import, unicode_literals, print_function
import argparse
from pkg_resources import resource_filename
from .readable import readables_from_paths
from .processpool import do
from .extractor import ExtractorFromEntryPoints
from .output import ExtractToStdout, ExtractToStdoutSavingOutput


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



def main():
    """ The main 'wex' command """

    import logging.config ; logging.config.fileConfig(default_logging_conf)

    args = argparser.parse_args()
    extractor = ExtractorFromEntryPoints(args.excluded_entry_points)
    if args.save:
        extract = ExtractToStdoutSavingOutput(extractor, args.responses_dir)
    else:
        extract = ExtractToStdout(extractor)

    readables = readables_from_paths(args.paths, args.save, args.responses_dir)
    do(extract, readables, pool_size=args.process_pool)
