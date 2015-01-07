import sys
import re
from .composed import composable
from .iterable import flatten

for name in dir(re):
    if name.isupper() and not name.startswith('_'):
        setattr(sys.modules[__name__], name, getattr(re, name))


def re_group(pattern, group=1, flags=0):
    """
    Returns a :mod:`composable <wex.composed>` callable that 
    extract the specified group using a regular expression.

    :param pattern: The regular expression.
    :param group: The group from the `MatchObject <https://docs.python.org/2/library/re.html#re.MatchObject.group>`_.
    :param flags: Flags to use when compiling the 
                        `pattern <https://docs.python.org/2/library/re.html#re.compile>`_.
    """
    compiled = re.compile(pattern, flags)
    @composable
    def regroup(src):
        for string in flatten(src):
            for match in compiled.finditer(string):
                yield match.group(group)
    return regroup


def re_groupdict(pattern, flags=0):
    """
    Returns a :mod:`composable <wex.composed>` callable that 
    extract the a group dictionary using a regular expression.

    :param pattern: The regular expression.
    :param flags: Flags to use when compiling the 
                        `pattern <https://docs.python.org/2/library/re.html#re.compile>`_.
    """
    compiled = re.compile(pattern, flags)
    compiled = re.compile(pattern, flags)
    @composable
    def redict(src):
        for string in flatten(src):
            for match in compiled.finditer(string):
                yield match.groupdict()
    return redict
