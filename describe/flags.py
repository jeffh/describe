""" flags.py - Various constants that have special meaning in describe.

INIT   - Represents a matcher be instanciated for initialization purposes only
NO_ARG - Represents no argument. This is Noner than None.
"""
class _Flag(object):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return 'flag(%s)' % self.name

INIT = _Flag('INIT')
NO_ARG = _Flag('NO_ARG')

# used for argument matching
ANY_ARG = _Flag('ANY_ARG')
ANYTHING = _Flag('ANYTHING')
ANY_ARGS = _Flag('ANY_ARGS')
ANY_KWARGS = _Flag('ANY_KWARGS')

def is_flag(value):
    return value in (INIT, NO_ARG, ANY_ARG, ANYTHING, ANY_ARGS, ANY_KWARGS)
