import sys
import re
from .composed import composable

for name in dir(re):
    if name.isupper() and not name.startswith('_'):
        setattr(sys.modules[__name__], name, getattr(re, name))


def group(pattern, group=1, flags=0):
    compiled = re.compile(pattern, flags)
    @composable
    def regroup(s):
        return (match.group(group) for match in compiled.finditer(s))
    return regroup


def groupdict(pattern, flags=0):
    compiled = re.compile(pattern, flags)
    @composable
    def redict(s):
        return (match.groupdict() for match in compiled.finditer(s))
    return redict
