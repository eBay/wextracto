""" The ``wex`` command extracts data from HTTP-like responses.
These responses can come from files, directories or URLs specified on the
command line.  The command calls any :mod:`extractors <wex.extractor>` that have
been :mod:`registered <wex.entrypoints>` and writes any data extracted
as :mod:`output <wex.output>`.

The output and input can be saved, using the ``--save`` or ``--save-dir``
command line arguments.  This is useful for
`regression testing <http://en.wikipedia.org/wiki/Regression_testing>`_.
existing extractor functions.
The test are run using :mod:`py.test <wex.pytestplugin>`.

For the complete list of command line arguments run:

.. code-block:: shell

    $ wex --help

"""
from __future__ import absolute_import, unicode_literals, print_function
import errno
import argparse
import logging.config
from multiprocessing import cpu_count
from pkg_resources import resource_filename
from .readable import readables_from_paths
from .response import Response
from .processpool import do
from .output import StdOut, TeeStdOut
from .value import Value
from .entrypoints import extractor_from_entry_points


default_logging_conf = resource_filename(__name__, 'logging.conf')


argparser = argparse.ArgumentParser()

argparser.add_argument(
    'paths',
    metavar='path',
    nargs='+',
    help="file, directory or url from which to extract"
)

save_group = argparser.add_argument_group("Save extraction input and output")

save_excl_group = save_group.add_mutually_exclusive_group()

save_excl_group.add_argument(
    '-s', '--save',
    action='store_const',
    dest='save_dir',
    const='saved',
    default=False,
    help="into directory 'saved'",
)

save_excl_group.add_argument(
    '--save-dir',
    dest='save_dir',
    metavar="DIR",
    help="into directory DIR",
)

process_pool_size_group = argparser.add_argument_group('Parallel processing using multiprocessing.Pool')

process_pool_size = process_pool_size_group.add_mutually_exclusive_group()

process_pool_size.add_argument(
    '-P',
    dest='process_pool_size',
    action="store_const",
    const=cpu_count(),
    default=1,
    help="with default pool size (default: %s)" % cpu_count(),
)

process_pool_size.add_argument(
    '--process-pool',
    dest='process_pool_size',
    metavar='N',
    type=int,
    default=1,
    help="with a pool size of N",
)

on_exc_group = argparser.add_argument_group("When an exception occurs")
on_exc = on_exc_group.add_mutually_exclusive_group()

on_exc.add_argument(
    '-x', '--exit-on-exc',
    action="store_true",
    default=False,
    help="exit with a traceback",
)

on_exc.add_argument(
    '-d', '--debug-on-exc',
    action="store_true",
    default=False,
    help="start the debugger",
)


class WriteExtractedValues(object):

    def __init__(self, stdout, extract):
        self.stdout = stdout
        self.extract = extract

    def __call__(self, readable):

        retval = None
        try:

            with self.stdout(readable) as writer:
                for value in Response.values_from_readable(self.extract, readable):
                    for line in value.text():
                        writer.write(line)

        except IOError as exc:

            # when we get an IOError it means we need to stop extracting
            # so we *return* an exception so that the processpool.do can
            # finish doing work.

            if exc.errno == errno.EPIPE:
                # unix convention is that exit code 0 is correct for a broken pipe
                retval = SystemExit(0)
            else:
                logging.getLogger(__name__).exception('reading %r', readable)
                retval = SystemExit(exc)

        except Exception as exc:
            logging.getLogger(__name__).exception('while extracting from %r', readable)
            raise

        return retval


def main():

    logging.config.fileConfig(default_logging_conf,
                              disable_existing_loggers=False)

    args = argparser.parse_args()
    extract = extractor_from_entry_points()
    if args.save_dir:
        func = WriteExtractedValues(TeeStdOut, extract)
    else:
        func = WriteExtractedValues(StdOut, extract)
    Value.exit_on_exc = args.exit_on_exc
    Value.debug_on_exc = args.debug_on_exc

    readables = readables_from_paths(args.paths, args.save_dir)
    do(func, readables, pool_size=args.process_pool_size)
